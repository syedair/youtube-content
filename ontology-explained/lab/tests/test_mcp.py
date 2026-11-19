"""Episode 7's MCP server (ep07_context_for_ai/graph_mcp.py) and the agent that calls it.

The server really starts over stdio and answers from the graph; the agent's model turns are recorded
(data/llm/ep07_agent.json), its tool calls run live through MCP.
"""
import asyncio
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent
SERVER = LAB / "ep07_context_for_ai" / "graph_mcp.py"
RECORDING = LAB / "data" / "llm" / "ep07_agent.json"


def load_step():
    spec = importlib.util.spec_from_file_location("ep07_mcp_step", LAB / "ep07_context_for_ai" / "step.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(LAB))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(LAB))
    return mod


async def with_server(work):
    from mcp import Client, StdioServerParameters

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with Client(params) as client:
        return await work(client)


def text_of(result) -> str:
    return "\n".join(b.text for b in result.content)


def test_server_starts_over_stdio_and_lists_its_tools():
    async def work(c):
        return (await c.list_tools()).tools

    tools = {t.name: t for t in asyncio.run(with_server(work))}
    assert sorted(tools) == ["hipaa_training", "people_on_projects"]
    assert tools["people_on_projects"].input_schema["required"] == ["product", "industry"]
    assert not tools["hipaa_training"].input_schema.get("properties")
    assert all(t.description for t in tools.values())


def test_tools_answer_from_the_graph():
    async def work(c):
        people = await c.call_tool("people_on_projects", {"product": "Cirrus AI", "industry": "healthcare"})
        loud = await c.call_tool("people_on_projects", {"product": "CIRRUS AI", "industry": " Healthcare"})
        none = await c.call_tool("people_on_projects", {"product": "Cirrus AI", "industry": "finance"})
        bank = await c.call_tool("people_on_projects", {"product": "Cirrus SQL", "industry": "finance"})
        training = await c.call_tool("hipaa_training", {})
        return people, loud, none, bank, training

    people, loud, none, bank, training = asyncio.run(with_server(work))
    assert text_of(people).splitlines() == [
        "Emma Clarke (Consultant): lead on Claims AI for Acme Health",
        "Daniel Brooks (Chief Architect): reviewer on Claims AI for Acme Health",
    ]
    assert text_of(loud) == text_of(people)  # matched lower-case
    assert text_of(none) == "No projects use Cirrus AI for finance customers."
    assert text_of(bank) == "Daniel Brooks (Chief Architect): lead on Lakehouse for Globex Bank"
    # the same values as the episode's SPARQL retrieval (step.py), one source: lab/data/cloudnova
    assert text_of(training).splitlines() == ["Daniel Brooks: HIPAA training done", "Emma Clarke: HIPAA training due"]
    assert not any(r.is_error for r in (people, loud, none, bank, training))


def test_bad_arguments_are_a_tool_error_not_a_crash():
    async def work(c):
        return await c.call_tool("people_on_projects", {"product": "Cirrus AI"})

    assert asyncio.run(with_server(work)).is_error


def test_recording_is_raw_model_turns():
    turns = json.loads(RECORDING.read_text(encoding="utf-8"))
    assert [sorted(t) for t in turns] == [["content", "tool_calls"]] * len(turns)
    assert turns[-1]["tool_calls"] == [] and turns[-1]["content"]
    calls = [c for t in turns[:-1] for c in t["tool_calls"]]
    assert {c["name"] for c in calls} <= {"people_on_projects", "hipaa_training"}
    assert all(isinstance(json.loads(c["arguments"]), dict) for c in calls)


def test_agent_runs_the_recorded_calls_live_through_mcp(monkeypatch):
    monkeypatch.setenv("LAB_LLM", "recorded")
    monkeypatch.delenv("LAB_LLM_DIR", raising=False)
    s = load_step()
    trace, calls, answer = asyncio.run(s.agent())
    turns = json.loads(RECORDING.read_text(encoding="utf-8"))
    assert [(name, args) for name, args, _ in calls] == [
        (c["name"], json.loads(c["arguments"])) for t in turns for c in t["tool_calls"]]
    assert answer == turns[-1]["content"].strip()
    assert "tools it offers:" in trace and "  people_on_projects(product, industry)" in trace
    # every result printed is what the live server says now
    assert "graph says:          Daniel Brooks: HIPAA training done" in trace
    assert " " * 21 + "Emma Clarke: HIPAA training due" in trace


def test_agent_offers_the_mcp_tools_to_the_model(monkeypatch):
    s = load_step()
    seen = []

    def fake_chat(messages, tools, *, name, turn):
        seen.append((messages[-1], tools, name, turn))
        return {"content": "Emma.", "tool_calls": []}

    monkeypatch.setattr(s, "chat", fake_chat)
    trace, calls, answer = asyncio.run(s.agent())
    (last, tools, name, turn), = seen
    assert last == {"role": "user", "content": s.QUESTION} and name == "ep07_agent" and turn == 0
    assert sorted(t["function"]["name"] for t in tools) == ["hipaa_training", "people_on_projects"]
    assert all(t["type"] == "function" and t["function"]["parameters"]["type"] == "object" for t in tools)
    assert calls == [] and answer == "Emma."


def test_agent_sends_tool_results_back_and_stops_after_max_turns(monkeypatch):
    s = load_step()
    sent = []

    def fake_chat(messages, tools, *, name, turn):
        sent.append(list(messages))
        return {"content": "", "tool_calls": [{"id": f"c{turn}", "name": "hipaa_training", "arguments": "{}"}]}

    monkeypatch.setattr(s, "chat", fake_chat)
    trace, calls, answer = asyncio.run(s.agent())
    assert len(calls) == s.MAX_TURNS and answer == ""
    assert trace[-1] == f"no answer: the model was still calling tools after {s.MAX_TURNS} turns"
    tool_msg = sent[1][-1]
    assert tool_msg["role"] == "tool" and tool_msg["tool_call_id"] == "c0"
    assert "Emma Clarke: HIPAA training due" in tool_msg["content"]
