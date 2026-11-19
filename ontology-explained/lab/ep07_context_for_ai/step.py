"""Episode 7: context for AI. The same question to an LLM with no context, with chunks a keyword search
finds in the company's documents, and with facts from the graph; then to an agent that calls the graph
itself, as tools, through an MCP server (graph_mcp.py)."""
import json
import logging
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.io import LAB_ROOT, load_cloudnova, name_list, number, sections, verdict  # noqa: E402
from common.llm import ask, chat  # noqa: E402

logging.disable(logging.CRITICAL)

QUESTION = "Which employees built Cirrus AI solutions for healthcare customers, and who still needs HIPAA training?"

RETRIEVE = """\
PREFIX cn:   <https://data.cloudnova.example/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?name ?relation ?engagement ?customer ?product ?training
WHERE { ?e a cn:Engagement ;
           cn:forCustomer ?c ;
           cn:uses ?p ;
           rdfs:label ?engagement .
        ?c cn:industry "healthcare" ; rdfs:label ?customer .
        ?p rdfs:label "Cirrus AI" , ?product .
        { ?e cn:hasLead ?who . BIND("lead" AS ?relation) }
        UNION
        { ?e cn:hasReviewer ?who . BIND("reviewer" AS ?relation) }
        ?who rdfs:label ?name ;
             cn:hipaaTraining ?training . }
ORDER BY ?relation ?name"""

TRAINING = {"trained": "done", "due": "due"}

# Search: the company's documents, cut into chunks (one per paragraph), ranked by BM25 keyword score.
# Real systems usually rank by vector similarity instead; the idea is the same: text similar to the question.
DOCS = LAB_ROOT / "data" / "cloudnova" / "docs"
TOP_K = 3
STOPWORDS = set("a an and are as at be by for from in is it its of on or that the to which who with".split())

SEARCH_PROMPT = """\
Answer the question using only the documents below. Do not use anything else you know. \
Cite the documents you rely on by quoting them. \
If the documents do not answer the question, say so.

Documents:
{chunks}

Question: {question}"""


SERVER = Path(__file__).resolve().parent / "graph_mcp.py"
AGENT_SYSTEM = """\
You answer questions about Cloudnova, a company. You know nothing about it yourself. \
Get every fact from the tools; they read Cloudnova's knowledge graph. \
When you have the facts, answer from those facts only."""
MAX_TURNS = 6


def retrieve() -> list[dict]:
    g = load_cloudnova()
    return [
        {k: str(v) for k, v in zip(("name", "relation", "engagement", "customer", "product", "training"), row)}
        for row in g.query(RETRIEVE)
    ]


def facts_block(rows: list[dict]) -> str:
    return "\n".join(
        f"{r['name']} — {r['relation']}, {r['engagement']} ({r['customer']}, {r['product']})"
        f" — HIPAA training: {TRAINING.get(r['training'], r['training'])}"
        for r in rows
    )


def chunks() -> list[tuple[str, str]]:
    """(document name, paragraph) for every paragraph of every document, in name order."""
    out = []
    for doc in sorted(DOCS.glob("*.txt")):
        for para in re.split(r"\n\s*\n", doc.read_text(encoding="utf-8")):
            if para.strip():
                out.append((doc.name, " ".join(para.split())))
    return out


def words(text: str) -> list[str]:
    """Lower-case words, without the small ones that say nothing about the topic (STOPWORDS)."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS]


def ranked(found: list[tuple[str, str]], scores: list[float], k: int = TOP_K) -> list[tuple[float, str, str]]:
    """The k best-scoring chunks, as (score, document, text)."""
    top = sorted(zip(scores, found), key=lambda x: -x[0])[:k]
    return [(score, doc, text) for score, (doc, text) in top]


def search(query: str, k: int = TOP_K) -> tuple[list[tuple[float, str, str]], int]:
    """The top k chunks for the query, as (score, document, text), and how many chunks there were.

    The ranking is BM25, in keyword_search.py (runnable by itself; it imports from this file)."""
    from ep07_context_for_ai.keyword_search import bm25

    found = chunks()
    return ranked(found, bm25(query, [text for _doc, text in found]), k), len(found)


def show_search(found: list[tuple[str, str]], scores: list[float], rows: list[dict] | None = None):
    """Print the search section: the top chunks, the model's answer from them, and the verdict."""
    rows = retrieve() if rows is None else rows
    top = ranked(found, scores)
    answer = ask(SEARCH_PROMPT.format(chunks=chunks_block(top), question=QUESTION), name="ep07_search").strip()
    lines = [f"{number(len(sorted(DOCS.glob('*.txt')))).capitalize()} documents in data/cloudnova/docs, "
             f"cut into {len(found)} chunks (one per paragraph).",
             f"Keyword search (BM25) for the question; the top {number(len(top))}:"]
    lines += [f"  {k}. {doc}  score {score:.1f}  \"{first_words(text)}\""
              for k, (score, doc, text) in enumerate(top, 1)]
    lines += ["The model's answer, from those chunks only:", answer]
    print("== WITH SEARCH OVER DOCUMENTS ==\n" + "\n".join(lines))
    verdict(*verdict_search(answer, top, rows))


def chunks_block(top: list[tuple[float, str, str]]) -> str:
    return "\n".join(f"[{doc}] {text}" for _score, doc, text in top)


def first_words(text: str, n: int = 8) -> str:
    w = text.split()
    return " ".join(w[:n]) + (" ..." if len(w) > n else "")


# models write the apostrophe straight (can't) or curly (can’t)
DECLINES = re.compile(r"(?i)\b(can['’]t|cannot|can not|unable|don['’]t know|do not know|no information)\b")


def first_names(rows: list[dict]) -> list[str]:
    """The retrieved people's first names, in retrieval order, once each."""
    return list(dict.fromkeys(r["name"].split()[0] for r in rows))


def named(answer: str, rows: list[dict]) -> list[str]:
    """Which of the retrieved people an answer names (by first name)."""
    return [n for n in first_names(rows) if re.search(rf"\b{re.escape(n)}\b", answer)]


def verdict_question():
    return None, "A question about our own company's data, not the public web."


def verdict_facts(rows: list[dict]):
    due = [r["name"].split()[0] + "'s" for r in rows if TRAINING.get(r["training"], r["training"]) == "due"]
    who = name_list(due) + " training is due" if due else "nobody's training is due"
    return None, f"From the graph: {name_list(first_names(rows))} worked on it; {who}."


def verdict_without(answer: str, rows: list[dict]):
    """The answer without the graph: does it name anyone, or decline?"""
    names = named(answer, rows)
    if names:
        return None, f"No context, yet it names {name_list(names)}: a guess, not a source."
    if DECLINES.search(answer):
        return None, "No context: the model cannot answer."
    return None, "No context: it names none of the real people."


def verdict_with(answer: str, rows: list[dict]):
    names = named(answer, rows)
    if names:
        return None, f"With the facts, it names {name_list(names)}."
    return None, "With the facts, it still names nobody."


NEEDS = re.compile(r"(?i)\b(due|needs?|still|must|not yet|yet to|has not|hasn['’]t)\b")
DONE = re.compile(r"(?i)\b(done|completed|has finished|trained)\b")


def claims(answer: str, rows: list[dict]) -> tuple[list[str], list[str]]:
    """What an answer says, sentence by sentence: who it names for the work (sentences without "training"),
    and who it says still needs the training."""
    built, due = [], []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        names = named(sentence, rows)
        if "training" not in sentence.lower():
            built += names
        elif NEEDS.search(sentence) and not DONE.search(sentence):
            due += names
    return list(dict.fromkeys(built)), list(dict.fromkeys(due))


def verdict_search(answer: str, top: list, rows: list[dict]):
    """The answer from the searched chunks, against the graph: who worked on it, whose training is due."""
    built, said_due = claims(answer, rows)
    missing = [n for n in first_names(rows) if n not in built]
    due = [r["name"].split()[0] for r in rows if TRAINING.get(r["training"], r["training"]) == "due"]
    lead = f"Search found {number(len(top))} similar chunk{'s' if len(top) != 1 else ''}"
    if sorted(said_due) == sorted(due):
        training = f"gets {name_list(due)}'s training" if due else "gets the training right"
        if not missing:
            return None, f"{lead}; it names {name_list(built)} and {training}."
        if not built:
            return None, f"{lead}; it {training}, not who built it."
        return None, f"{lead}; it {training} but misses {name_list(missing)}."
    if not missing:
        return None, f"{lead}; it names {name_list(built)} but not who needs training."
    return None, f"{lead}; it misses {name_list(missing)} and who needs training."


def verdict_agent(calls: list[tuple], answer: str, rows: list[dict]):
    """calls: (tool, arguments, result) for each MCP tool call the model made."""
    if not calls:
        return None, "No tool calls: the model answered without the graph."
    names = named(answer, rows)
    said = f"the answer names {name_list(names)}" if names else "yet the answer names nobody"
    n = len(calls)
    return None, f"{number(n).capitalize()} tool call{'s' if n != 1 else ''} through MCP; {said}."


def call_text(name: str, arguments: dict | str) -> str:
    """people_on_projects(product="Cirrus AI", industry="healthcare")"""
    if not isinstance(arguments, dict):
        return f"{name}({arguments})"
    return f"{name}(" + ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in arguments.items()) + ")"


def indent(label: str, text: str) -> list[str]:
    """'label text' with the text's further lines lined up under its first."""
    pad = " " * len(label)
    return [(label if k == 0 else pad) + line for k, line in enumerate(text.splitlines() or [""])]


async def agent() -> tuple[list[str], list[tuple], str]:
    """Start the MCP server over stdio, offer its tools to the model, run the calls it asks for.

    Returns the printed trace, the calls (tool, arguments, result) and the model's final answer. The
    model's turns are recorded (common.llm.chat); the MCP server and its answers are always live.
    """
    from mcp import Client, StdioServerParameters

    out = [f"MCP server: {SERVER.parent.name}/{SERVER.name}, started over stdio", "tools it offers:"]
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    calls, answer = [], ""
    async with Client(params) as mcp:
        listed = (await mcp.list_tools()).tools
        tools = [{"type": "function", "function": {"name": t.name, "description": t.description,
                                                   "parameters": t.input_schema}} for t in listed]
        for t in listed:
            out.append(f"  {t.name}(" + ", ".join(t.input_schema.get("properties", {})) + ")")
            out.append(f"    {t.description}")
        out.append(f"question: {QUESTION}")
        messages = [{"role": "system", "content": AGENT_SYSTEM}, {"role": "user", "content": QUESTION}]
        for turn in range(MAX_TURNS):
            reply = chat(messages, tools, name="ep07_agent", turn=turn)
            if not reply.get("tool_calls"):
                answer = reply.get("content", "").strip()
                out.append(f"model answers (turn {turn + 1}):")
                out.append(answer)
                break
            messages.append({"role": "assistant", "content": reply.get("content") or "", "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}}
                for c in reply["tool_calls"]]})
            for c in reply["tool_calls"]:
                try:
                    args = json.loads(c["arguments"] or "{}")
                except json.JSONDecodeError:
                    args = c["arguments"]
                result = await mcp.call_tool(c["name"], args if isinstance(args, dict) else {})
                text = "\n".join(getattr(b, "text", "") for b in result.content).strip()
                calls.append((c["name"], args, text))
                out.append(f"model asks (turn {turn + 1}): " + call_text(c["name"], args))
                out += indent("graph says:          ", text)
                messages.append({"role": "tool", "tool_call_id": c["id"], "content": text})
        else:
            out.append(f"no answer: the model was still calling tools after {MAX_TURNS} turns")
    return out, calls, answer


def main():
    only = sections(["question", "sparql", "facts", "without", "search", "with", "agent"])
    want = lambda name: only is None or name in only  # noqa: E731
    rows = retrieve() if any(want(n) for n in ("facts", "without", "search", "with", "agent")) else []
    # every section but the query text is its own short file, runnable by itself (they import from this file):
    # ask_alone.py prints the question and the model's answer alone, graph_facts.py the retrieved facts,
    # keyword_search.py the search, grounding.py the grounded answer, agent.py the agent
    from ep07_context_for_ai import agent as agent_run
    from ep07_context_for_ai import ask_alone, graph_facts, grounding, keyword_search

    blocks = []  # (a short file, the ask_alone parts it prints) or (printed text, None)
    for slug, module in (("question", ask_alone), ("sparql", None), ("facts", graph_facts),
                         ("without", ask_alone), ("search", keyword_search), ("with", grounding),
                         ("agent", agent_run)):
        if not want(slug):
            continue
        if module is None:
            blocks.append(("== sparql: retrieve the facts from the graph ==\n" + RETRIEVE, None))
        elif module is ask_alone and blocks and blocks[-1][0] is ask_alone:
            blocks[-1] = (ask_alone, blocks[-1][1] + (slug,))  # question and answer next to each other: one run
        else:
            blocks.append((module, (slug,) if module is ask_alone else None))
    for k, (block, parts) in enumerate(blocks):
        if k:
            print()
        if isinstance(block, str):
            print(block)
        elif parts:
            block.main(rows, parts)
        else:
            block.main(rows)


if __name__ == "__main__":
    main()
