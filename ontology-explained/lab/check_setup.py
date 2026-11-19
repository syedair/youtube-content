"""Setup check: run `uv run check_setup.py` from lab/ once after cloning.

Prints the Python version and the installed version of each library the lab uses, whether a local Ollama is
reachable (optional: only LAB_LLM=ollama needs it), then one verdict line. It contacts nothing but this machine:
an OLLAMA_BASE_URL on another host is reported, not called.
"""
import os
import socket
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common.io import name_list, verdict  # noqa: E402

PACKAGES = ["rdflib", "pyshacl", "owlrl", "networkx", "morph-kgc", "pypdf", "openai"]
LOCAL = {"localhost", "127.0.0.1", "::1"}
WIDTH = 11


def ollama_status() -> str:
    url = urlparse(os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"))
    host, port = url.hostname or "localhost", url.port or 11434
    if host not in LOCAL:
        return "optional: not checked (not on this machine)"
    try:
        socket.create_connection((host, port), timeout=0.5).close()
    except OSError:
        return "optional: not running (only for LAB_LLM=ollama)"
    return f"running at {host}:{port} (LAB_LLM=ollama can use it)"


def verdict_setup(missing: list[str]):
    if not missing:
        return True, "lab ready"
    are = "is" if len(missing) == 1 else "are"
    return False, f"lab not ready: {name_list(missing)} {are} missing. Run uv sync, then retry."


def main():
    print("== check: what the lab needs ==")
    print(f"{'python':<{WIDTH}}{sys.version.split()[0]}")
    missing = []
    for name in PACKAGES:
        try:
            print(f"{name:<{WIDTH}}{version(name)}")
        except PackageNotFoundError:
            print(f"{name:<{WIDTH}}missing")
            missing.append(name)
    print(f"{'ollama':<{WIDTH}}{ollama_status()}")
    verdict(*verdict_setup(missing))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
