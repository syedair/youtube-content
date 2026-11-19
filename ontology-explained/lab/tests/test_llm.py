import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import llm  # noqa: E402


@pytest.fixture
def llm_dir(tmp_path, monkeypatch):
    (tmp_path / "fixture_answer.txt").write_text("recorded answer é", encoding="utf-8")
    monkeypatch.setenv("LAB_LLM_DIR", str(tmp_path))
    return tmp_path


def test_llm_default_is_recorded(llm_dir, monkeypatch):
    monkeypatch.delenv("LAB_LLM", raising=False)

    def boom(*a, **k):
        raise AssertionError("network used in recorded mode")

    monkeypatch.setattr(socket, "create_connection", boom)
    assert llm.ask("x", name="fixture_answer") == "recorded answer é"


def test_llm_unreachable_is_friendly(llm_dir, monkeypatch, capsys):
    monkeypatch.setenv("LAB_LLM", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:9/v1")
    with pytest.raises(SystemExit) as e:
        llm.ask("x", name="fixture_answer")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "Can't reach the model at http://127.0.0.1:9/v1" in err
    assert "LAB_LLM=recorded" in err


def test_llm_missing_recording_is_friendly(llm_dir, monkeypatch, capsys):
    monkeypatch.setenv("LAB_LLM", "recorded")
    with pytest.raises(SystemExit) as e:
        llm.ask("x", name="nope_missing")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "nope_missing.txt" in err
    assert "LAB_RECORD=1" in err
    assert len(err.strip().splitlines()) == 1


def test_llm_client_is_hardened(llm_dir, monkeypatch):
    import openai

    seen = {}

    class Fake:
        def __init__(self, **kw):
            seen.update(kw)
            self.chat = self
            self.completions = self

        def create(self, **kw):
            seen.update(kw)
            raise openai.APIConnectionError(request=None)

    monkeypatch.setattr(openai, "OpenAI", Fake)
    monkeypatch.setenv("LAB_LLM", "ollama")
    with pytest.raises(SystemExit):
        llm.ask("x", name="fixture_answer")
    assert seen["temperature"] == 0
    assert seen["max_retries"] == 1
    assert seen["timeout"].connect == 5 and seen["timeout"].read == 60


def test_llm_model_not_installed_is_friendly(llm_dir, monkeypatch, capsys):
    import httpx2
    import openai

    class Fake:
        def __init__(self, **kw):
            self.chat = self
            self.completions = self

        def create(self, **kw):
            req = httpx2.Request("POST", "http://x/v1/chat/completions")
            raise openai.NotFoundError(
                "model not found", response=httpx2.Response(404, request=req), body=None
            )

    monkeypatch.setattr(openai, "OpenAI", Fake)
    monkeypatch.setenv("LAB_LLM", "ollama")
    monkeypatch.setenv("LAB_MODEL", "llama3.1:8b")
    with pytest.raises(SystemExit) as e:
        llm.ask("x", name="fixture_answer")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert "llama3.1:8b" in err and "ollama pull llama3.1:8b" in err
    assert "LAB_LLM=recorded" in err
    assert len(err.strip().splitlines()) == 1


def _fake_client(seen, exc=None):
    class Fake:
        def __init__(self, **kw):
            seen.update(kw)
            self.chat = self
            self.completions = self

        def create(self, **kw):
            raise exc
    return Fake


def test_llm_openai_without_key_uses_placeholder(llm_dir, monkeypatch):
    import openai

    seen = {}
    monkeypatch.setattr(openai, "OpenAI", _fake_client(seen, openai.APIConnectionError(request=None)))
    monkeypatch.setenv("LAB_LLM", "openai")
    for value in (None, ""):
        if value is None:
            monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        else:
            monkeypatch.setenv("OPENAI_API_KEY", value)
        with pytest.raises(SystemExit):
            llm.ask("x", name="fixture_answer")
        assert seen["api_key"] == "not-needed"


@pytest.mark.parametrize("status,cls", [(401, "AuthenticationError"), (403, "PermissionDeniedError"),
                                        (429, "RateLimitError"), (500, "InternalServerError")])
def test_llm_api_status_error_is_friendly(llm_dir, monkeypatch, capsys, status, cls):
    import httpx2
    import openai

    req = httpx2.Request("POST", "http://x/v1/chat/completions")
    exc = getattr(openai, cls)("nope", response=httpx2.Response(status, request=req), body=None)
    monkeypatch.setattr(openai, "OpenAI", _fake_client({}, exc))
    monkeypatch.setenv("LAB_LLM", "openai")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://x/v1")
    with pytest.raises(SystemExit) as e:
        llm.ask("x", name="fixture_answer")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert len(err.strip().splitlines()) == 1
    assert str(status) in err and "http://x/v1" in err and "LAB_LLM=recorded" in err


# ---- chat(): one turn of a tool-using conversation (the episode 7 agent)

TURNS = [{"content": "", "tool_calls": [{"id": "c1", "name": "hipaa_training", "arguments": "{}"}]},
         {"content": "Emma é.", "tool_calls": []}]


def test_chat_replays_recorded_turns(llm_dir, monkeypatch):
    import json

    (llm_dir / "agent.json").write_text(json.dumps(TURNS), encoding="utf-8")
    monkeypatch.delenv("LAB_LLM", raising=False)

    def boom(*a, **k):
        raise AssertionError("network used in recorded mode")

    monkeypatch.setattr(socket, "create_connection", boom)
    assert llm.chat([], [], name="agent", turn=0) == TURNS[0]
    assert llm.chat([], [], name="agent", turn=1) == TURNS[1]


def test_chat_missing_or_short_recording_is_friendly(llm_dir, monkeypatch, capsys):
    import json

    monkeypatch.setenv("LAB_LLM", "recorded")
    with pytest.raises(SystemExit) as e:
        llm.chat([], [], name="nope_agent", turn=0)
    assert e.value.code == 2 and "nope_agent.json" in capsys.readouterr().err
    (llm_dir / "agent.json").write_text(json.dumps(TURNS), encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        llm.chat([], [], name="agent", turn=2)
    err = capsys.readouterr().err
    assert e.value.code == 2 and "Traceback" not in err and "LAB_RECORD=1" in err
    assert len(err.strip().splitlines()) == 1


def test_chat_live_sends_tools_and_records_each_turn(llm_dir, monkeypatch):
    import json
    from types import SimpleNamespace as NS

    import openai

    seen = []
    replies = [NS(content=None, tool_calls=[NS(id="c1", function=NS(name="hipaa_training", arguments="{}"))]),
               NS(content="Emma.", tool_calls=None)]

    class Fake:
        def __init__(self, **kw):
            self.chat = self
            self.completions = self

        def create(self, **kw):
            seen.append(kw)
            return NS(choices=[NS(message=replies[len(seen) - 1])])

    monkeypatch.setattr(openai, "OpenAI", Fake)
    monkeypatch.setenv("LAB_LLM", "ollama")
    monkeypatch.setenv("LAB_RECORD", "1")
    tools = [{"type": "function", "function": {"name": "hipaa_training", "parameters": {"type": "object"}}}]
    msgs = [{"role": "user", "content": "q"}]
    assert llm.chat(msgs, tools, name="rec", turn=0) == TURNS[0]
    assert llm.chat(msgs, tools, name="rec", turn=1) == {"content": "Emma.", "tool_calls": []}
    assert seen[0]["tools"] == tools and seen[0]["messages"] == msgs and seen[0]["temperature"] == 0
    saved = json.loads((llm_dir / "rec.json").read_text(encoding="utf-8"))
    assert saved == [TURNS[0], {"content": "Emma.", "tool_calls": []}]
    # recording again from turn 0 starts a fresh file
    replies[0] = NS(content="Just text.", tool_calls=None)
    seen.clear()
    llm.chat(msgs, tools, name="rec", turn=0)
    assert json.loads((llm_dir / "rec.json").read_text(encoding="utf-8")) == [
        {"content": "Just text.", "tool_calls": []}]
