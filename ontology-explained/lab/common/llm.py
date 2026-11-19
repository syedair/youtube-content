"""One tiny LLM client: recorded answers by default, a live model on request.

LAB_LLM=recorded (default) | ollama | openai. LAB_RECORD=1 saves the live answer.
`ask` sends one prompt and gets text back; `chat` sends a conversation plus tools and gets one turn back
(text, or the tool calls the model wants), for the episode 7 agent.
"""
import json
import os
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent


def llm_dir() -> Path:
    return Path(os.environ.get("LAB_LLM_DIR") or LAB_ROOT / "data" / "llm")


def _missing(path: Path) -> SystemExit:
    print(
        f"No recorded answer {path.name} in {path.parent}. "
        "Record it with LAB_LLM=ollama LAB_RECORD=1.",
        file=sys.stderr,
    )
    return SystemExit(2)


def _live(**request):
    """One chat completion from the live model (LAB_LLM=ollama | openai); friendly errors, no tracebacks."""
    mode = os.environ.get("LAB_LLM", "recorded")
    if mode == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        api_key = "ollama"
    elif mode == "openai":
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        api_key = os.environ.get("OPENAI_API_KEY") or "not-needed"  # local OpenAI-compatible servers need none
    else:
        raise SystemExit(f"Unknown LAB_LLM={mode!r}. Use recorded, ollama or openai.")
    from openai import APIConnectionError, APIStatusError, NotFoundError, OpenAI, Timeout

    client = OpenAI(base_url=base_url, api_key=api_key,
                    timeout=Timeout(60, connect=5), max_retries=1)
    model = os.environ.get("LAB_MODEL", "llama3.1:8b")
    try:
        resp = client.chat.completions.create(model=model, temperature=0, **request)
    except NotFoundError:
        print(
            f"The model {model!r} isn't available at {base_url}. "
            f"Run `ollama pull {model}`, or use LAB_LLM=recorded for saved answers.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    except APIStatusError as e:  # 401 bad key, 403, 429 rate limit, 5xx ...
        print(
            f"The model at {base_url} answered HTTP {e.status_code} ({type(e).__name__}). "
            "Check OPENAI_API_KEY and LAB_MODEL, or run with LAB_LLM=recorded to use saved answers.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    except APIConnectionError:
        print(
            f"Can't reach the model at {base_url}. "
            "Run with LAB_LLM=recorded to use saved answers.",
            file=sys.stderr,
        )
        raise SystemExit(2) from None
    return resp.choices[0].message


def ask(prompt: str, *, name: str) -> str:
    mode = os.environ.get("LAB_LLM", "recorded")
    path = llm_dir() / f"{name}.txt"
    if mode == "recorded":
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise _missing(path) from None
    text = _live(messages=[{"role": "user", "content": prompt}]).content or ""
    if os.environ.get("LAB_RECORD") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text


def chat(messages: list[dict], tools: list[dict], *, name: str, turn: int) -> dict:
    """One model turn in a tool-using conversation: {"content": text, "tool_calls": [{id, name, arguments}]}.

    `arguments` is the JSON text the model wrote. Recorded mode replays turn `turn` of `<name>.json`
    (a list, one entry per turn); LAB_RECORD=1 with a live model saves each turn there as it happens.
    """
    mode = os.environ.get("LAB_LLM", "recorded")
    path = llm_dir() / f"{name}.json"
    if mode == "recorded":
        try:
            turns = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise _missing(path) from None
        if turn >= len(turns):
            print(f"{path.name} has {len(turns)} recorded turns; the conversation needs turn {turn + 1}. "
                  "Record it again with LAB_LLM=ollama LAB_RECORD=1.", file=sys.stderr)
            raise SystemExit(2)
        return turns[turn]
    msg = _live(messages=messages, tools=tools)
    reply = {
        "content": msg.content or "",
        "tool_calls": [{"id": c.id, "name": c.function.name, "arguments": c.function.arguments}
                       for c in (msg.tool_calls or [])],
    }
    if os.environ.get("LAB_RECORD") == "1":
        turns = json.loads(path.read_text(encoding="utf-8")) if turn and path.is_file() else []
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(turns[:turn] + [reply], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return reply
