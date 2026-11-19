"""What you see is what you run: each demo prints a short module with `cat`, then runs that same module.

Each module runs by itself and prints exactly its sections of the step's golden output; step.py runs the same
module for those sections; and the module stays short enough to read on screen.
"""
import ast
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_steps import MODULE_ARGS, MODULES, load_step, module_slice

LAB = Path(__file__).resolve().parent.parent
MAX_LINES = 30
MAX_COLS = 80
CASES = [(step, mod, slugs) for (step, mod), slugs in MODULES.items()]
ARG_CASES = [(step, mod, arg, slugs) for (step, mod, arg), slugs in MODULE_ARGS.items()]


def ids(rows):
    return [f"{step}/{mod}.py" for step, mod, _s in rows]


@pytest.mark.parametrize("step,mod,arg,slugs", ARG_CASES, ids=[f"{s}/{m}.py {a}" for s, m, a, _ in ARG_CASES])
def test_module_runs_on_another_file(step, mod, arg, slugs, monkeypatch, capsys):
    # the same code the demo just showed, now on another input file: it prints that file's sections ...
    assert (step, mod) in MODULES and (LAB / arg).is_file()
    r = subprocess.run(["uv", "run", f"{step}/{mod}.py", arg], cwd=LAB, capture_output=True, timeout=600,
                       env={**os.environ, "LAB_LLM": "recorded"})
    assert r.returncode == 0, r.stderr.decode()
    assert r.stdout.decode("utf-8") == module_slice(step, slugs)
    # ... and step.py runs it the same way, on the same file, for those sections
    s = load_step(step)
    sys.path.insert(0, str(LAB))
    try:
        module = importlib.import_module(f"{step}.{mod}")
    finally:
        sys.path.remove(str(LAB))
    calls = []
    real = module.main
    monkeypatch.setattr(module, "main", lambda *a, **k: calls.append(a) or real(*a, **k))
    monkeypatch.setattr(sys, "argv", ["step.py", "--only", ",".join(slugs)])
    s.main()
    assert calls == [(arg,)]
    assert capsys.readouterr().out.rstrip("\n") + "\n" == module_slice(step, slugs)


@pytest.mark.parametrize("step,mod,slugs", CASES, ids=ids(CASES))
def test_module_runs_by_itself_and_prints_its_sections(step, mod, slugs):
    r = subprocess.run(["uv", "run", f"{step}/{mod}.py"], cwd=LAB, capture_output=True, timeout=600,
                       env={**os.environ, "LAB_LLM": "recorded"})
    assert r.returncode == 0, r.stderr.decode()
    assert r.stdout.decode("utf-8") == module_slice(step, slugs)


@pytest.mark.parametrize("step,mod,slugs", CASES, ids=ids(CASES))
def test_step_runs_the_module(step, mod, slugs, monkeypatch, capfd):
    # capfd, not capsys: agent.py starts the MCP server as a subprocess, which needs a real stderr
    s = load_step(step)
    sys.path.insert(0, str(LAB))
    try:
        module = importlib.import_module(f"{step}.{mod}")
    finally:
        sys.path.remove(str(LAB))
    assert Path(module.__file__) == LAB / step / f"{mod}.py"
    calls = []
    real = module.main
    monkeypatch.setattr(module, "main", lambda *a, **k: calls.append(a) or real(*a, **k))
    monkeypatch.setattr(sys, "argv", ["step.py", "--only", ",".join(slugs)])
    monkeypatch.setenv("LAB_LLM", "recorded")
    monkeypatch.delenv("LAB_API", raising=False)
    s.main()
    out = capfd.readouterr().out
    assert len(calls) == 1, f"step.py --only {','.join(slugs)} did not run {mod}.py"
    assert out.rstrip("\n") + "\n" == module_slice(step, slugs)


@pytest.mark.parametrize("step,mod,_slugs", CASES, ids=ids(CASES))
def test_module_is_short_and_plain(step, mod, _slugs):
    path = LAB / step / f"{mod}.py"
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) <= MAX_LINES, f"{path.name}: {len(lines)} lines, want at most {MAX_LINES}"
    for n, line in enumerate(lines, 1):
        assert len(line) <= MAX_COLS, f"{path.name}:{n} is {len(line)} characters"
    doc = ast.get_docstring(ast.parse(text))
    assert doc and "\n" not in doc, f"{path.name}: needs a one-line docstring"
    assert lines[0].startswith('"""') and lines[0].endswith('"""')
    assert 'if __name__ == "__main__":' in text  # runnable by itself
    assert "noqa" not in text  # nothing on screen but the code


def test_every_module_is_listed():
    # any .py next to a step.py (other than the MCP server, shown with head) is a runnable module
    found = {(p.parent.name, p.stem) for p in LAB.glob("ep*/*.py") if p.name not in ("step.py", "graph_mcp.py")}
    assert found == set(MODULES)


@pytest.mark.parametrize("step,mod,slugs", CASES, ids=ids(CASES))
def test_readme_runs_the_module_first(step, mod, slugs):
    run_it = (LAB / step / "README.md").read_text(encoding="utf-8").split("## Run it")[1].split("\n## ")[0]
    assert f"uv run {step}/{mod}.py" in run_it
    assert run_it.index(f"uv run {step}/{mod}.py") < run_it.index(f"uv run {step}/step.py")
