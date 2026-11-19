"""Golden-output harness: every ep*/step.py is tested with no per-episode code."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent
STEPS = sorted(LAB.glob("ep*/step.py"))
IGNORE = shutil.ignore_patterns("out", ".venv", "__pycache__", ".pytest_cache")


def ids(steps):
    return [s.parent.name for s in steps]


def run(lab: Path, step: Path, **env):
    full = {**os.environ, "LAB_LLM": "recorded", **env}
    rel = step.relative_to(lab) if step.is_absolute() else step
    return subprocess.run(
        ["uv", "run", str(rel)], cwd=lab, env=full, capture_output=True, timeout=600
    )


def golden(step: Path) -> str:
    return (step.parent / "expected.txt").read_text(encoding="utf-8")


def test_steps_exist():
    assert STEPS, "no ep*/step.py found"


@pytest.mark.parametrize("step", STEPS, ids=ids(STEPS))
def test_step_matches_golden(step):
    r = run(LAB, step)
    assert r.returncode == 0, r.stderr.decode()
    assert r.stdout.decode("utf-8") == golden(step)


@pytest.mark.parametrize("step", STEPS, ids=ids(STEPS))
def test_step_runs_in_fresh_copy(step, tmp_path):
    dest = tmp_path / "lab"
    shutil.copytree(LAB, dest, ignore=IGNORE)
    r = run(dest, step.relative_to(LAB))
    assert r.returncode == 0, r.stderr.decode()
    assert r.stdout.decode("utf-8") == golden(step)


@pytest.mark.parametrize("step", STEPS, ids=ids(STEPS))
def test_output_utf8_under_c_locale(step):
    r = run(LAB, step, LC_ALL="C", LANG="C")
    assert r.returncode == 0, r.stderr.decode()
    assert r.stdout.decode("utf-8") == golden(step)


# --only sections: slug -> the heading prefixes that belong to it (the section runs from its
# heading to the next heading of another section). Same names as the "Run it" lists in each README.
SECTIONS = {
    "ep01_context": {"sources": ["sources"], "naive-join": ["naive join"], "one-id": ["one ID"],
                     "family-id": ["family ID"]},
    "ep02_facts": {"merge": ["merge"], "turtle": ["turtle"], "n-triples": ["n-triples"], "json-ld": ["json-ld"]},
    "ep03_meaning": {"inferred": ["inferred by RDFS"], "trap": ["trap"], "clash": ["clash"]},
    "ep04_think_check": {"reason": ["reason"], "check": ["check: Dad"], "fix": ["check: after the fix"],
                         "rule": ["rule"]},
    "ep05_ask": {"sparql": ["sparql"], "property-graph": ["property graph"],
                 "algorithms": ["graph algorithms"]},
    "ep06_real_data": {"map": ["map"], "semantic-layer": ["semantic layer"],
                       "api": ["api"], "pdf": ["pdf"], "extract": ["the LLM reads"], "gate": ["SHACL gate"],
                       "match": ["match"]},
    "ep07_context_for_ai": {"question": ["the question"], "sparql": ["sparql"], "facts": ["retrieved facts"],
                            "without": ["WITHOUT"], "search": ["WITH SEARCH"], "with": ["WITH THE"],
                            "agent": ["agent"]},
    "ep08_production": {"ci": ["ontology CI"], "diff": ["version diff"], "provenance": ["provenance"],
                        "taxonomy": ["taxonomy"]},
    "ep09_design": {"cq1": ["CQ1"], "cq2": ["CQ2"], "cq3": ["CQ3"], "cq4": ["CQ4"], "rule": ["rule"]},
}

# The short files next to a step, each runnable by itself (`uv run <step dir>/<module>.py`): the sections it
# prints, in order. step.py runs them for those sections. The demos show each with `cat`, then run it.
MODULES = {
    ("ep01_context", "sources"): ["sources"],
    ("ep01_context", "exact_match"): ["naive-join"],
    ("ep01_context", "lookup"): ["one-id"],
    ("ep02_facts", "merge"): ["merge"],
    ("ep02_facts", "formats"): ["turtle", "n-triples", "json-ld"],
    ("ep03_meaning", "rdfs_infer"): ["trap"],
    ("ep03_meaning", "reasoner"): ["clash"],
    ("ep04_think_check", "shacl_check"): ["check"],
    ("ep05_ask", "ask_sparql"): ["sparql"],
    ("ep05_ask", "property_graph"): ["property-graph"],
    ("ep05_ask", "graph_algorithms"): ["algorithms"],
    ("ep06_real_data", "fetch_api"): ["api"],
    ("ep06_real_data", "read_pdf"): ["pdf"],
    ("ep06_real_data", "extract"): ["extract"],
    ("ep06_real_data", "shape_gate"): ["gate"],
    ("ep07_context_for_ai", "ask_alone"): ["question", "without"],
    ("ep07_context_for_ai", "graph_facts"): ["facts"],
    ("ep07_context_for_ai", "keyword_search"): ["search"],
    ("ep07_context_for_ai", "grounding"): ["with"],
    ("ep07_context_for_ai", "agent"): ["agent"],
    ("ep08_production", "ci_checks"): ["ci"],
    ("ep08_production", "diff_versions"): ["diff"],
    ("ep08_production", "taxonomy"): ["taxonomy"],
}
# A module run with a lab-relative file (`uv run <step dir>/<module>.py <file>`): the same code on another input,
# and the sections it prints then. step.py runs it the same way for those sections.
MODULE_ARGS = {
    ("ep04_think_check", "shacl_check", "data/carter/dad-spreadsheet-fixed.csv"): ["fix"],
}


def module_slice(step_dir: str, slugs: list[str]) -> str:
    """The golden lines a module prints: its sections' slices, as one block, without trailing blank lines."""
    prefixes = [p for slug in slugs for p in SECTIONS[step_dir][slug]]
    return expected_slice(LAB / step_dir / "step.py", prefixes).rstrip("\n") + "\n"


def expected_slice(step: Path, prefixes: list[str]) -> str:
    """Lines of expected.txt from the section's heading up to the next heading of another section."""
    lines = golden(step).splitlines(keepends=True)
    out, inside = [], False
    for line in lines:
        if line.startswith("== "):
            inside = any(line[3:].startswith(p) for p in prefixes)
        if inside:
            out.append(line)
    return "".join(out)


ONLY_CASES = [(ep, slug) for ep, secs in SECTIONS.items() for slug in secs]


def test_sections_table_covers_every_step():
    assert sorted(SECTIONS) == sorted(s.parent.name for s in STEPS)


@pytest.mark.parametrize("ep,slug", ONLY_CASES, ids=[f"{e}-{s}" for e, s in ONLY_CASES])
def test_only_section_is_slice_of_golden(ep, slug):
    step = LAB / ep / "step.py"
    r = subprocess.run(["uv", "run", f"{ep}/step.py", "--only", slug], cwd=LAB,
                       env={**os.environ, "LAB_LLM": "recorded"}, capture_output=True, timeout=600)
    assert r.returncode == 0, r.stderr.decode()
    want = expected_slice(step, SECTIONS[ep][slug])
    assert want, f"no heading found for {ep} {slug}"
    assert r.stdout.decode("utf-8").rstrip("\n") == want.rstrip("\n")


@pytest.mark.parametrize("ep", sorted(SECTIONS))
def test_only_unknown_section_lists_valid_names(ep):
    r = subprocess.run(["uv", "run", f"{ep}/step.py", "--only", "nope"], cwd=LAB, capture_output=True, timeout=600)
    assert r.returncode == 2
    assert r.stdout == b""
    err = r.stderr.decode()
    assert all(slug in err for slug in SECTIONS[ep])


@pytest.mark.parametrize("ep", sorted(SECTIONS))
def test_readme_run_it_lists_sections(ep):
    text = (LAB / ep / "README.md").read_text(encoding="utf-8")
    run_it = text.split("## Run it")[1].split("## ")[0]
    assert "--only" in run_it
    assert all(f"`{slug}`" in run_it for slug in SECTIONS[ep])


def test_ep01_no_naive_matches():
    step = LAB / "ep01_context" / "step.py"
    out = run(LAB, step).stdout.decode("utf-8")
    assert "exact-match pairs: 0" in out
    for name in ["Nana", "Rose C.", "CARTER, ROSE", "R. Lee", "Mom"]:
        assert name in out


def test_ep01_acme_names_match_episode_6():
    # the four systems episode 6 also matches spell Acme the same way in both episodes
    import csv
    with open(LAB / "data" / "cloudnova" / "acme-names.csv", encoding="utf-8", newline="") as f:
        ep06 = {r["source"]: r["name"] for r in csv.DictReader(f)}
    with open(LAB / "data" / "cloudnova" / "who-is-who.csv", encoding="utf-8", newline="") as f:
        table = list(csv.DictReader(f))
    assert len(table) == 5 and {r["id"] for r in table} == {"acme-health"}
    shared = {r["system"]: r["name"] for r in table if r["system"] in ep06}
    assert len(shared) == 4 and all(ep06[k] == v for k, v in shared.items())
    out = run(LAB, LAB / "ep01_context" / "step.py").stdout.decode("utf-8").split("== one ID")[1]
    assert "before the table, exact-match pairs: 0" in out and "distinct customers: 1" in out
    for r in table:
        assert f'"{r["name"]}"' in out


def test_common_io_utf8_under_c_locale():
    env = {k: v for k, v in os.environ.items() if k != "PYTHONIOENCODING"}
    env.update(LC_ALL="C", LANG="C")
    code = "import common.io; common.io.show('Léa', ['→ • ✓'])"
    r = subprocess.run(
        ["uv", "run", "python", "-c", code],
        cwd=LAB, env=env, capture_output=True, timeout=600,
    )
    assert r.returncode == 0, r.stderr.decode()
    out = r.stdout.decode("utf-8")
    assert "Léa" in out and "→ • ✓" in out


def test_out_dir_creates_missing_dir(tmp_path, monkeypatch):
    sys.path.insert(0, str(LAB))
    import common.io as cio

    root = tmp_path / "labcopy"
    monkeypatch.setattr(cio, "LAB_ROOT", root)
    assert not (root / "out").exists()
    d = cio.out_dir()
    assert d == root / "out" and d.is_dir()
    assert cio.out_dir() == d  # idempotent


def test_ep02_merge():
    out = run(LAB, LAB / "ep02_facts" / "step.py").stdout.decode("utf-8")
    assert "fam:rose-carter children: fam:david-carter, fam:maya-carter" in out
    assert "distinct Rose nodes after merge: 1" in out
    assert "merged graph: 10 triples" in out
    assert "triple count (all formats): 9" in out
    for marker in ["== turtle ==", "== n-triples ==", "== json-ld =="]:
        assert marker in out


def test_ep03_domain_range():
    out = run(LAB, LAB / "ep03_meaning" / "step.py").stdout.decode("utf-8")
    assert "fam:toronto a fam:Place (inferred from range)" in out


def load_step(epdir: str):
    """Import a step by file path under a unique module name (no sys.path mutation)."""
    import importlib.util

    path = LAB / epdir / "step.py"
    spec = importlib.util.spec_from_file_location(f"{epdir}_step", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(LAB))  # steps import `common`; restored below
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(LAB))
    return mod


def _ep04():
    return load_step("ep04_think_check")


def test_ep04_reasoning():
    out = run(LAB, LAB / "ep04_think_check" / "step.py").stdout.decode("utf-8")
    assert "fam:leo-carter fam:hasAncestor fam:rose-carter (inferred)" in out
    assert "fam:tom-carter fam:marriedTo fam:rose-carter (inferred)" in out


def test_ep04_shacl():
    from rdflib import XSD, Literal

    s = _ep04()
    bad = s.dad_row()
    conforms, rows = s.violations(bad)
    assert conforms is False and len(rows) == 1
    assert "fam:birthDate" in rows[0] and '"03/04/31"' in rows[0]
    rose = s.FAM["rose-carter"]
    bad.set((rose, s.FAM.birthDate, Literal("1931-04-03", datatype=XSD.date)))
    assert s.violations(bad)[0] is True
    # the fix is a real file: the same row with the date written as a real date
    fixed = s.dad_row("dad-spreadsheet-fixed.csv")
    assert fixed.value(rose, s.FAM.birthDate) == Literal("1931-04-03", datatype=XSD.date)
    assert s.violations(fixed) == (True, [])
    before, after = ((LAB / "data" / "carter" / n).read_text().splitlines() for n in ("dad-spreadsheet.csv", "dad-spreadsheet-fixed.csv"))
    assert before[0] == after[0] and before[1].replace("03/04/31", "1931-04-03") == after[1]


def test_ep04_rule():
    s = _ep04()
    g = s.family()
    made = {(str(a), str(c)) for a, _, c in g.query(s.GRANDPARENT_RULE)}
    fam = s.FAM
    assert made == {
        (str(fam["rose-carter"]), str(fam["amy-carter"])),
        (str(fam["rose-carter"]), str(fam["leo-carter"])),
    }


def test_ep05_grandchildren():
    out = run(LAB, LAB / "ep05_ask" / "step.py").stdout.decode("utf-8")
    assert "Rose's grandchildren: Amy, Leo" in out
    # the query is a file the demo shows with `cat`; the step names it rather than printing it again
    assert "== sparql: Rose's grandchildren (ep05_ask/grandchildren.rq) ==" in out
    assert "SELECT ?gc" in (LAB / "ep05_ask" / "grandchildren.rq").read_text()


def test_ep05_algorithms():
    out = run(LAB, LAB / "ep05_ask" / "step.py").stdout.decode("utf-8")
    assert "most central: Daniel Brooks" in out
    assert (
        "shortest path Emma Clarke → Globex Bank: "
        "Emma Clarke → Claims AI → Daniel Brooks → Lakehouse → Globex Bank"
    ) in out


def test_load_cloudnova_facts():
    from rdflib import Literal

    s = load_step("ep05_ask")
    g = s.load_cloudnova()
    from common.ns import CN
    assert (CN.emma, CN.hipaaTraining, Literal("due")) in g
    assert (CN["claims-ai"], CN.hasReviewer, CN.daniel) in g
    assert (CN["acme-health"], CN.industry, Literal("healthcare")) in g


def test_ep06_mapping():
    out = run(LAB, LAB / "ep06_real_data" / "step.py").stdout.decode("utf-8")
    assert "mapped triples:" in out
    assert "cn:claims-ai cn:forCustomer cn:acme-health" in out


def test_ep06_semantic_layer():
    s = load_step("ep06_real_data")
    # three reports, three numbers for one word...
    found = {name: customers for name, _rule, customers in s.reports()}
    assert found == {"sales dashboard": ["Acme Health"],
                     "consulting team sheet": ["Acme Health", "Globex Bank", "Initech"],
                     "finance report": ["Acme Health", "Globex Bank"]}
    # ...and one definition (metrics.ttl, over the mapped graph) with one number
    label, definition, counted = s.metric(s.map_tables())
    assert label == "Active customers" and definition == "a signed contract and an open engagement"
    assert counted == ["Acme Health", "Globex Bank"]


def test_ep06_match_names():
    s = load_step("ep06_real_data")
    names, pairs, rows = s.match_names(["Acme Health", "Globex Bank", "Initech"])
    assert len(names) == 5 and pairs == 15 and len(rows) == 5  # blocking: only the Acme pairs are scored
    got = {name: (score, ok) for score, name, _src, _c, ok in rows}
    assert got == {"ACME Health": (1.0, True), "ACME-HLTH": (0.9, True), "Acme Health Inc.": (0.85, True),
                   "Acme": (0.53, False), "Acme Hospital Group": (0.53, False)}
    assert s.normal("ACME-HLTH") == "acme hlth"


def test_ep09_rule_has_owner_reason_and_date():
    from rdflib import Graph

    s = load_step("ep09_design")
    shapes = Graph().parse(s.RULE, format="turtle")
    card = s.rule_card(shapes)
    assert str(card["owner"]) == "CloudNova compliance team" and str(card["since"]) == "2026-10-31"
    assert "patient data" in str(card["why"])
    # the rule flags the same person CQ4 names
    assert s.flagged(s.load_cloudnova(labs=True), shapes) == ["Emma Clarke"]


def test_ep06_extraction_caught():
    out = run(LAB, LAB / "ep06_real_data" / "step.py").stdout.decode("utf-8")
    recorded = (LAB / "data" / "llm" / "ep06_extract.txt").read_text(encoding="utf-8")
    assert 'cn:startDate "2026-13-01"' in recorded
    assert "sh:datatype xsd:date" in out
    assert "quarantined: 1" in out


def test_ep06_extraction_gate_keeps_good_triples():
    s = load_step("ep06_real_data")
    from common.ns import CN

    mapped = s.map_tables()
    extracted = s.parse_turtle(s.extraction())
    accepted, quarantined = s.gate(extracted, mapped)
    assert len(quarantined) == 1 and quarantined[0][1] == CN.startDate
    assert (CN["claims-ai"], CN.startDate, None) not in accepted
    assert (CN["claims-ai"], CN.hasLead, CN.emma) in accepted


def test_ep07_context():
    s = load_step("ep07_context_for_ai")
    facts = s.facts_block(s.retrieve())
    assert facts.splitlines() == [
        "Emma Clarke — lead, Claims AI (Acme Health, Cirrus AI) — HIPAA training: due",
        "Daniel Brooks — reviewer, Claims AI (Acme Health, Cirrus AI) — HIPAA training: done",
    ]


def test_ep07_side_by_side_prints_both_answers():
    out = run(LAB, LAB / "ep07_context_for_ai" / "step.py").stdout.decode("utf-8")
    assert out.index("WITHOUT THE GRAPH") < out.index("WITH THE GRAPH")
    llm = LAB / "data" / "llm"
    assert (llm / "ep07_without.txt").read_text(encoding="utf-8").strip() in out
    assert (llm / "ep07_with.txt").read_text(encoding="utf-8").strip() in out
    assert "Which employees built Cirrus AI solutions for healthcare customers, and who still needs HIPAA training?" in out


def test_ep07_search_ranks_chunks_by_keywords():
    s = load_step("ep07_context_for_ai")
    from ep07_context_for_ai.keyword_search import bm25  # the step put the lab folder on sys.path

    found = s.chunks()
    docs = sorted(p.name for p in s.DOCS.glob("*.txt"))
    assert len(docs) == 5 and {d for d, _t in found} == set(docs) and len(found) == 16
    top, n = s.search(s.QUESTION)
    assert n == 16 and len(top) == s.TOP_K == 3
    assert [d for _s, d, _t in top] == ["hipaa-training-reminder.txt", "hipaa-training-reminder.txt",
                                        "acme-health-account-note.txt"]
    assert [round(x, 1) for x, _d, _t in top] == [5.3, 4.3, 4.0]
    # the staffing line (who leads, who reviews) shares no word with the question, so it scores zero
    texts = [t for _d, t in found]
    staffing = next(k for k, t in enumerate(texts) if t.startswith("Staffing:"))
    assert bm25(s.QUESTION, texts)[staffing] == 0
    # BM25 by hand: a chunk without the word scores nothing, and a rarer word scores more
    assert bm25("hipaa", ["hipaa training", "training", "other words"])[1:] == [0, 0]
    chunks = ["rare common", "common", "common"]
    assert bm25("rare", chunks)[0] > bm25("common", chunks)[0]
    assert s.words("Who built the Cirrus AI?") == ["built", "cirrus", "ai"]


def test_ep07_search_documents_agree_with_the_data():
    # the documents are what a company would write; their facts are the lab's facts
    s = load_step("ep07_context_for_ai")
    text = {p.name: " ".join(p.read_text(encoding="utf-8").split()) for p in s.DOCS.glob("*.txt")}
    assert "Emma Clarke will lead the engagement. Daniel Brooks will act as reviewer." in text["sow-17-summary.txt"]
    assert "period 13, day 1 (P13 D1)" in text["sow-17-summary.txt"]
    assert "Daniel Brooks leads the project" in text["patient-360-project-page.txt"]
    assert "Cirrus Graph" in text["patient-360-project-page.txt"]
    assert "Industry: healthcare" in text["acme-health-account-note.txt"]
    assert "signed 2025-03-14" in text["acme-health-account-note.txt"]
    assert "your HIPAA training is due" in text["hipaa-training-reminder.txt"]
    sql = (LAB / "data" / "cloudnova" / "cloudnova.sql").read_text()
    for row in ("('emma', 'Emma Clarke', 'Consultant', 'due')",
                "('daniel', 'Daniel Brooks', 'Chief Architect', 'trained')",
                "('claims-ai', 'Claims AI', 'acme-health', 'cirrus-ai', 'emma', 'daniel', 'open')",
                "('patient-360', 'Patient 360', 'acme-health', 'cirrus-graph', 'daniel', NULL, 'open')",
                "('acme-health', 'Acme Health', 'healthcare')", "('msa-acme-health', 'acme-health', '2025-03-14')"):
        assert row in sql, row


def test_ep07_search_prints_the_chunks_and_the_recorded_answer():
    out = run(LAB, LAB / "ep07_context_for_ai" / "step.py").stdout.decode("utf-8")
    assert out.index("WITHOUT THE GRAPH") < out.index("WITH SEARCH OVER DOCUMENTS") < out.index("WITH THE GRAPH")
    assert (LAB / "data" / "llm" / "ep07_search.txt").read_text(encoding="utf-8").strip() in out
    assert '1. hipaa-training-reminder.txt  score 5.3  "Hi Emma, from today anyone who leads or ..."' in out


def test_ep07_unknown_training_value_is_tolerated():
    s = load_step("ep07_context_for_ai")
    row = dict(name="Zed", relation="lead", engagement="X", customer="Y", product="Z", training="overdue")
    assert s.facts_block([row]).endswith("HIPAA training: overdue")


def test_ep06_component_reads_datatype_from_shape():
    from rdflib import SH, XSD

    s = load_step("ep06_real_data")
    assert s.component(SH.DatatypeConstraintComponent) == "sh:datatype xsd:date"
    assert s.shape_datatype() == XSD.date


def test_load_cloudnova_tolerates_engagement_without_lead():
    from rdflib import RDF, Literal

    from common.ns import CN
    s = load_step("ep05_ask")
    g = s.load_cloudnova()
    assert (CN["fraud-watch"], RDF.type, CN.Engagement) in g
    assert not list(g.objects(CN["fraud-watch"], CN.hasLead))


def test_ep08_ci():
    out = run(LAB, LAB / "ep08_production" / "step.py").stdout.decode("utf-8")
    assert "ontology CI: SHACL ✓  competency queries 4/4 ✓" in out
    assert "+ fam:hasAncestor a owl:TransitiveProperty" in out


def test_ep08_provenance():
    out = run(LAB, LAB / "ep08_production" / "step.py").stdout.decode("utf-8")
    assert 'fam:rose-carter fam:birthName "Rose Lee"  ← source: census-1951.csv' in out


def test_ep08_skos_taxonomy_is_kind_of_only():
    out = run(LAB, LAB / "ep08_production" / "step.py").stdout.decode("utf-8")
    assert "cn:cirrus-ai is a kind of cn:ai-services" in out


def test_ep08_v2_is_the_shipped_ontology():
    from rdflib import Graph
    from rdflib.compare import isomorphic

    v2 = Graph().parse(LAB / "ep08_production" / "family-v2.ttl", format="turtle")
    cur = Graph().parse(LAB / "data" / "ontology" / "family.ttl", format="turtle")
    assert isomorphic(v2, cur)


def test_ep09_cqs():
    out = run(LAB, LAB / "ep09_design" / "step.py").stdout.decode("utf-8")
    for q in [
        "Which employees worked on Cirrus AI engagements for healthcare customers?",
        "Which engagements have no lead?",
        "Which lab results lack a valid LOINC code?",
        "Who needs HIPAA training?",
    ]:
        assert q in out
    assert "Who needs HIPAA training?" in out
    block = out.split("Who needs HIPAA training?")[1]
    assert "Emma Clarke" in block
    assert "(no answer)" not in out


def test_competency_questions_single_source():
    s8 = load_step("ep08_production")
    s9 = load_step("ep09_design")
    from common.io import competency_questions

    cqs = competency_questions()
    assert [c[0] for c in cqs] == ["CQ1", "CQ2", "CQ3", "CQ4"]
    assert s8.competency_questions is competency_questions
    assert s9.competency_questions is competency_questions


@pytest.mark.parametrize("step", STEPS, ids=ids(STEPS))
def test_readme_has_required_headings(step):
    text = (step.parent / "README.md").read_text(encoding="utf-8")
    heads = [l[3:].strip() for l in text.splitlines() if l.startswith("## ")]
    assert heads == ["What you'll see", "Run it", "Expected output", "Try this"]


@pytest.mark.parametrize("only,maps", [("api", False), ("pdf", False), ("extract", False), ("pdf,api", False),
                                       ("match", False),
                                       ("map", True), ("semantic-layer", True), ("gate", True), (None, True)])
def test_ep06_maps_tables_only_when_a_section_needs_them(only, maps, monkeypatch, capsys):
    s = load_step("ep06_real_data")
    calls = []
    real = s.map_tables
    monkeypatch.setattr(s, "map_tables", lambda: calls.append(1) or real())
    monkeypatch.setattr(sys, "argv", ["step.py"] + (["--only", only] if only else []))
    monkeypatch.setenv("LAB_LLM", "recorded")
    monkeypatch.delenv("LAB_API", raising=False)
    s.main()
    assert len(calls) == (1 if maps else 0)
    capsys.readouterr()
