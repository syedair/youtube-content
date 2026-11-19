import socket
import subprocess
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LAB))
from common import sources  # noqa: E402


def test_api_default_is_recorded(monkeypatch):
    monkeypatch.delenv("LAB_API", raising=False)

    def boom(*a, **k):
        raise AssertionError("network used in recorded mode")

    monkeypatch.setattr(socket, "create_connection", boom)
    data = sources.fetch_json("https://www.wikidata.org/wiki/Special:EntityData/Q172.json", name="wikidata-Q172")
    assert data["entities"]["Q172"]["labels"]["en"]["value"] == "Toronto"


def test_api_unreachable_is_friendly(monkeypatch, capsys):
    monkeypatch.setenv("LAB_API", "live")
    monkeypatch.delenv("LAB_RECORD", raising=False)
    with pytest.raises(SystemExit) as e:
        sources.fetch_json("http://127.0.0.1:9/x.json", name="wikidata-Q172")
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err
    assert len(err.strip().splitlines()) == 1
    assert "LAB_API=recorded" in err


def test_api_unknown_mode_exits(monkeypatch):
    monkeypatch.setenv("LAB_API", "nope")
    with pytest.raises(SystemExit):
        sources.fetch_json("http://x", name="wikidata-Q172")


def test_pdf_text():
    text = sources.pdf_text(LAB / "data" / "docs" / "sow-17.pdf")
    assert "period 13, day 1" in text
    assert "STATEMENT OF WORK 17" in text


def test_sow_txt_is_the_pdf_text():
    # sow-17.txt is the readable copy the deck and README quote; it must say what the PDF says
    pdf = " ".join(sources.pdf_text(LAB / "data" / "docs" / "sow-17.pdf").split())
    txt = " ".join((LAB / "ep06_real_data" / "sow-17.txt").read_text(encoding="utf-8").split())
    assert pdf == txt


def test_ep06_api_and_pdf():
    r = subprocess.run(["uv", "run", "ep06_real_data/step.py"], cwd=LAB, capture_output=True, timeout=600,
                       env={**__import__("os").environ, "LAB_LLM": "recorded", "LAB_API": "recorded"})
    out = r.stdout.decode("utf-8")
    assert "fam:toronto → wd:Q172 Toronto, Canada (from Wikidata)" in out
    assert "source: sow-17.pdf" in out
