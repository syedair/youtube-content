"""Real-world sources for the lab: a JSON API (recorded or live) and a PDF.

LAB_API=recorded (default) | live. LAB_RECORD=1 with live saves the snapshot to data/api/<name>.json.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

LAB_ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "ontology-journey-lab/1.0 (https://github.com/syedair/youtube-content)"


def api_dir() -> Path:
    return Path(os.environ.get("LAB_API_DIR") or LAB_ROOT / "data" / "api")


def fetch_json(url: str, *, name: str, trim: Callable[[dict], dict] | None = None) -> dict:
    """GET a JSON document (recorded snapshot by default). `trim` keeps only the fields the lab uses;
    it is applied before a snapshot is saved, so the committed file is the real response, cut down."""
    mode = os.environ.get("LAB_API", "recorded")
    path = api_dir() / f"{name}.json"
    if mode == "recorded":
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(
                f"No recorded snapshot {path.name} in {path.parent}. "
                "Record it with LAB_API=live LAB_RECORD=1.",
                file=sys.stderr,
            )
            raise SystemExit(2) from None
    if mode != "live":
        raise SystemExit(f"Unknown LAB_API={mode!r}. Use recorded or live.")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        reason = getattr(e, "reason", e)
        print(f"Can't reach the API at {url} ({reason}). Run with LAB_API=recorded to use the saved snapshot.",
              file=sys.stderr)
        raise SystemExit(2) from None
    if trim:
        data = trim(data)
    if os.environ.get("LAB_RECORD") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data


def pdf_text(path: Path) -> str:
    """The text of every page of a PDF, via pypdf."""
    from pypdf import PdfReader

    return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)
