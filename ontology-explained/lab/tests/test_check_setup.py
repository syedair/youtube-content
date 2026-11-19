"""lab/check_setup.py: the setup check a new viewer runs first (`uv run check_setup.py` from lab/).

Versions differ from machine to machine, so these tests check the structure and the verdict, not numbers.
"""
import os
import re
import subprocess
from pathlib import Path

LAB = Path(__file__).resolve().parent.parent
PACKAGES = ["rdflib", "pyshacl", "owlrl", "networkx", "morph-kgc", "pypdf", "openai"]


def run(**extra):
    env = {k: v for k, v in os.environ.items() if k not in ("FORCE_COLOR", "NO_COLOR", "OLLAMA_BASE_URL")}
    env.update(extra)
    r = subprocess.run(["uv", "run", "check_setup.py"], cwd=LAB, env=env, capture_output=True, timeout=600)
    return r.returncode, r.stdout.decode("utf-8")


def test_lists_python_and_every_key_package_with_a_version():
    code, out = run(OLLAMA_BASE_URL="http://127.0.0.1:9/v1")
    assert code == 0, out
    lines = out.splitlines()
    assert lines[0] == "== check: what the lab needs =="
    assert re.fullmatch(r"python\s+3\.(1[2-9]|[2-9]\d)\.\d+", lines[1]), lines[1]
    for name, line in zip(PACKAGES, lines[2:9]):
        assert re.fullmatch(rf"{re.escape(name)}\s+\d+(\.\d+)+\S*", line), (name, line)


def test_ollama_is_optional_and_never_fails_the_check():
    code, out = run(OLLAMA_BASE_URL="http://127.0.0.1:9/v1")  # nothing listens on port 9
    assert code == 0
    assert re.search(r"^ollama\s+optional: not running \(only for LAB_LLM=ollama\)$", out, re.M), out
    assert out.splitlines()[-1] == "✓ lab ready"


def test_only_localhost_is_ever_contacted():
    # a remote OLLAMA_BASE_URL is reported, not called
    code, out = run(OLLAMA_BASE_URL="http://ollama.example.com:11434/v1")
    assert code == 0
    assert re.search(r"^ollama\s+optional: not checked \(not on this machine\)$", out, re.M), out


def test_verdict_is_green_with_force_color():
    _, out = run(OLLAMA_BASE_URL="http://127.0.0.1:9/v1", FORCE_COLOR="1")
    assert "\033[1;32m✓ lab ready\033[0m" in out
    _, plain = run(OLLAMA_BASE_URL="http://127.0.0.1:9/v1")
    assert "\033[" not in plain


def test_missing_package_is_a_red_verdict():
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("check_setup_under_test", LAB / "check_setup.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(LAB))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(LAB))
    assert mod.verdict_setup([]) == (True, "lab ready")
    assert mod.verdict_setup(["pypdf"]) == (False, "lab not ready: pypdf is missing. Run uv sync, then retry.")
    assert mod.verdict_setup(["pypdf", "owlrl"]) == (
        False, "lab not ready: pypdf and owlrl are missing. Run uv sync, then retry.")
