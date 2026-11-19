"""Plain-English verdict lines: after its real output, every section a terminal demo shows prints exactly
one line starting with "✓ ", "✗ " or "→ " that says what the result means (at most 14 words).

The lines are computed from the step's own values (conforms, counts, names), so they stay true when the
data changes; these tests feed the verdict functions other values to prove it.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

LAB = Path(__file__).resolve().parent.parent
MARKS = ("✓ ", "✗ ", "→ ")

# the sections the demos run (demos/*.sh) that end on a verdict
DEMO_SECTIONS = [
    ("ep01_context", "naive-join"), ("ep01_context", "one-id"), ("ep02_facts", "merge"), ("ep02_facts", "json-ld"),
    ("ep03_meaning", "trap"),
    ("ep03_meaning", "clash"), ("ep04_think_check", "check"), ("ep04_think_check", "fix"),
    ("ep05_ask", "sparql"), ("ep05_ask", "algorithms"), ("ep06_real_data", "api"), ("ep06_real_data", "pdf"),
    ("ep06_real_data", "extract"), ("ep06_real_data", "gate"), ("ep07_context_for_ai", "question"),
    ("ep07_context_for_ai", "facts"), ("ep07_context_for_ai", "without"), ("ep07_context_for_ai", "search"),
    ("ep07_context_for_ai", "with"),
    ("ep07_context_for_ai", "agent"),
    ("ep08_production", "ci"), ("ep08_production", "diff"), ("ep08_production", "taxonomy"),
]

# what each demo section's verdict says with the lab's data and recorded answers
WANT = {
    ("ep01_context", "naive-join"): "✗ The computer finds no match: five names, zero links.",
    ("ep01_context", "one-id"): "✓ Five names, one ID: the computer now sees one customer.",
    ("ep02_facts", "merge"): "✓ One Rose, not two: both files' facts now sit on one node.",
    ("ep02_facts", "json-ld"): "✓ Same 9 facts, three spellings: each reads back as the same graph.",
    ("ep03_meaning", "trap"): "✗ No error, no warning: RDFS made Globex Bank an Employee.",
    ("ep03_meaning", "clash"): "✗ CONTRADICTION: Globex Bank can't be a Person and an Organization.",
    ("ep04_think_check", "check"): '✗ REJECTED: "03/04/31" is not a real date. The rule wants 1931-04-03.',
    ("ep04_think_check", "fix"): "✓ ACCEPTED: the birth date is now a real date, 1931-04-03.",
    ("ep05_ask", "sparql"): "→ Rose has two grandchildren: Amy and Leo.",
    ("ep05_ask", "algorithms"): "→ Daniel Brooks sits on the most paths; Emma is four hops from Globex Bank.",
    ("ep06_real_data", "api"): "✓ Linked: our Toronto is Wikidata's Toronto, Canada (Q172).",
    ("ep06_real_data", "pdf"): "→ The PDF page is now seven lines of plain text for the LLM.",
    ("ep06_real_data", "extract"): "→ The LLM wrote six triples. Nothing has checked them yet.",
    ("ep06_real_data", "gate"): '✗ REJECTED: "2026-13-01" is not a real date. 5 of 6 triples kept.',
    ("ep07_context_for_ai", "question"): "→ A question about our own company's data, not the public web.",
    ("ep07_context_for_ai", "facts"): "→ From the graph: Emma and Daniel worked on it; Emma's training is due.",
    ("ep07_context_for_ai", "without"): "→ No context: the model cannot answer.",
    ("ep07_context_for_ai", "search"): "→ Search found three similar chunks; it gets Emma's training, not who built it.",
    ("ep07_context_for_ai", "with"): "→ With the facts, it names Emma.",
    ("ep07_context_for_ai", "agent"): "→ Two tool calls through MCP; the answer names Emma and Daniel.",
    ("ep08_production", "ci"): "✓ Passed: the data fits every shape, and all four questions get answers.",
    ("ep08_production", "diff"): "→ Six changes in meaning: one fact removed, five added.",
    ("ep08_production", "taxonomy"): "→ Three names, one service: Cirrus AI is a kind of AI services.",
}


def env(**extra):
    e = {k: v for k, v in os.environ.items() if k not in ("FORCE_COLOR", "NO_COLOR") and not k.startswith("LAB_")}
    e["LAB_LLM"] = "recorded"
    e.update(extra)
    return e


def run(step, slug=None, **extra):
    args = ["uv", "run", f"{step}/step.py"] + (["--only", slug] if slug else [])
    r = subprocess.run(args, cwd=LAB, env=env(**extra), capture_output=True, timeout=600)
    assert r.returncode == 0, r.stderr.decode()
    return r.stdout.decode("utf-8")


def verdicts(text):
    return [l for l in text.splitlines() if l.startswith(MARKS)]


def load_step(epdir):
    spec = importlib.util.spec_from_file_location(f"{epdir}_verdict_step", LAB / epdir / "step.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(LAB))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(LAB))
    return mod


@pytest.mark.parametrize("step,slug", DEMO_SECTIONS, ids=[f"{s}-{o}" for s, o in DEMO_SECTIONS])
def test_demo_section_prints_one_verdict(step, slug):
    lines = verdicts(run(step, slug))
    assert lines == [WANT[(step, slug)]]
    assert len(lines[0][2:].split()) <= 14, lines[0]


def test_verdicts_are_in_the_goldens():
    for (step, _slug), line in WANT.items():
        assert line + "\n" in (LAB / step / "expected.txt").read_text(encoding="utf-8"), (step, line)


def test_verdict_follows_the_technical_output():
    # the result comes first, then the line that says what it means
    out = run("ep04_think_check", "check")
    assert out.index("violation: ") < out.index("✗ REJECTED")
    out = run("ep01_context", "naive-join")
    assert out.index("exact-match pairs: 0") < out.index("✗ The computer") < out.index("Same person?")


def test_colour_only_when_forced_or_a_terminal():
    plain = run("ep04_think_check", "check")
    assert "\033[" not in plain
    red = run("ep04_think_check", "check", FORCE_COLOR="1")
    assert '\033[1;31m✗ REJECTED: "03/04/31"' in red and red.count("\033[0m") == 1
    green = run("ep04_think_check", "fix", FORCE_COLOR="1")
    assert "\033[1;32m✓ ACCEPTED" in green
    bold = run("ep05_ask", "sparql", FORCE_COLOR="1")
    assert "\033[1m→ Rose has" in bold
    assert "\033[" not in run("ep04_think_check", "check", FORCE_COLOR="1", NO_COLOR="1")
    assert "\033[" not in run("ep04_think_check", "check", FORCE_COLOR="0")


def test_number_words_and_name_lists():
    sys.path.insert(0, str(LAB))
    from common.io import name_list, number

    assert [number(n) for n in (0, 5, 12, 13)] == ["zero", "five", "twelve", "13"]
    assert name_list([]) == "nobody" and name_list(["Amy"]) == "Amy"
    assert name_list(["Amy", "Leo"]) == "Amy and Leo" and name_list(["A", "B", "C"]) == "A, B and C"


# ---- the lines are computed: other values give other (true) lines

def test_ep01_verdict_counts():
    s = load_step("ep01_context")
    assert s.verdict_join(5, 0) == (False, "The computer finds no match: five names, zero links.")
    ok, text = s.verdict_join(5, 1)  # the README's "try this": change Mom to Nana
    assert ok is None and text == "The computer links one pair of names, by exact spelling."
    assert s.verdict_one_id(5, {"rose-carter"}) == (True, "Five names, one ID: the computer now sees one person.")
    # the README's other "try this": give one row a different ID, or delete a row
    assert s.verdict_one_id(5, {"rose-carter", "rose-c"}) == (False, "Two IDs for one grandma: the table needs fixing.")
    assert s.verdict_one_id(5, {"rose-carter", None})[0] is False
    # the demo's Acme lookup says customer; a split Acme says so
    assert s.verdict_one_id(5, {"acme-health"}, "customer", "one customer") == (
        True, "Five names, one ID: the computer now sees one customer.")
    assert s.verdict_one_id(5, {"acme-health", "acme"}, "customer", "one customer") == (
        False, "Two IDs for one customer: the table needs fixing.")


def test_ep02_verdict_counts_roses():
    s = load_step("ep02_facts")
    assert s.verdict_formats([9, 9, 9], 9) == (True, "Same 9 facts, three spellings: each reads back as the same graph.")
    assert s.verdict_formats([9, 0, 9], 9) == (False, "A spelling lost facts on the way back: 9, 0, 9 of 9.")
    assert s.verdict_merge(1) == (True, "One Rose, not two: both files' facts now sit on one node.")
    assert s.verdict_merge(2) == (False, "Two Roses: the files did not merge.")


def test_ep03_verdicts():
    s = load_step("ep03_meaning")
    assert s.verdict_trap(0, ["Globex Bank"]) == (False, "No error, no warning: RDFS made Globex Bank an Employee.")
    assert s.verdict_trap(0, []) == (None, "RDFS only added types, and nothing looks out of place.")
    assert s.verdict_trap(2, []) == (True, "RDFS raised two errors.")
    clash = (s.CN["globex-bank"], s.CN.Person, s.CN.Organization)
    assert s.verdict_clash([clash]) == (False, "CONTRADICTION: Globex Bank can't be a Person and an Organization.")
    other = (s.CN["initech"], s.CN.Employee, s.CN.Customer)
    assert s.verdict_clash([other]) == (False, "CONTRADICTION: Initech can't be an Employee and a Customer.")
    assert s.verdict_clash([]) == (True, "CONSISTENT: nothing is in two classes that never overlap.")


def test_ep03_clash_comes_from_the_reasoner():
    # the contradiction is owlrl's own error message, not a string the step writes; RDFS alone finds none
    from rdflib import RDF

    s = load_step("ep03_meaning")
    from ep03_meaning import reasoner  # the step put the lab folder on sys.path

    g = s.cloudnova(owl=True)
    reasoner.reason(g, owl=True)  # reasoner.py: owlrl's OWL-RL closure, the code the demo shows
    assert reasoner.errors(g) == ["Disjoint classes https://data.cloudnova.example/Person and "
                                    "https://data.cloudnova.example/Organization have a common individual "
                                    "https://data.cloudnova.example/globex-bank"]
    rdfs = s.cloudnova(owl=False)
    reasoner.reason(rdfs, owl=False)
    assert reasoner.errors(rdfs) == []
    assert (s.CN["globex-bank"], RDF.type, s.CN.Employee) in rdfs


def test_ep04_verdicts_follow_conforms():
    s = load_step("ep04_think_check")
    assert s.verdict_check(*s.violations(s.dad_row())) == (
        False, 'REJECTED: "03/04/31" is not a real date. The rule wants 1931-04-03.')
    fixed = s.dad_row("dad-spreadsheet-fixed.csv")
    assert s.verdict_check(*s.violations(fixed)) == (True, "ACCEPTED: the row fits the rule.")
    born = fixed.value(s.FAM["rose-carter"], s.FAM.birthDate)
    assert s.verdict_fix(True, born) == (True, "ACCEPTED: the birth date is now a real date, 1931-04-03.")
    assert s.verdict_fix(False, born) == (False, 'REJECTED: "1931-04-03" still breaks the rule.')


def test_ep05_verdicts():
    s = load_step("ep05_ask")
    assert s.verdict_grandchildren(["Amy", "Leo"]) == (None, "Rose has two grandchildren: Amy and Leo.")
    assert s.verdict_grandchildren([]) == (None, "Rose has zero grandchildren: nobody.")
    path = ["Emma Clarke", "Claims AI", "Globex Bank"]
    assert s.verdict_algorithms("Daniel Brooks", path) == (
        None, "Daniel Brooks sits on the most paths; Emma is two hops from Globex Bank.")
    assert s.verdict_property_graph(3) == (None, "One link, three details: on the edge, or as RDF 1.2 notes.")
    assert s.verdict_property_graph(0) == (None, "A bare link: no details to carry.")


def test_ep05_property_graph_edge_carries_the_csv_details():
    # the details come from data/carter/marriage.csv; the RDF loader keeps only the triple
    s = load_step("ep05_ask")
    rdf, triple, pg = s.marriage()
    assert triple == (s.FAM["rose-carter"], s.FAM.marriedTo, s.FAM["tom-carter"])
    assert len(rdf) == 2  # Tom is a Person, and the bare marriage triple
    assert dict(pg["rose-carter"]["tom-carter"]["MARRIED_TO"]) == {
        "since": 1952, "place": "Toronto", "source": "marriage certificate"}


def test_ep06_verdicts():
    from rdflib import Graph, Literal

    s = load_step("ep06_real_data")
    assert s.verdict_api("Toronto", "Canada") == (True, "Linked: our Toronto is Wikidata's Toronto, Canada (Q172).")
    assert s.verdict_pdf("a\nb\n\n") == (None, "The PDF page is now two lines of plain text for the LLM.")
    assert s.verdict_extract("```\nnot turtle at all\n```") == (False, "The LLM's answer is not valid Turtle.")
    extracted = s.parse_turtle(s.extraction())
    assert s.verdict_gate(extracted, extracted, []) == (True, "ACCEPTED: all six triples fit the shape.")
    mapped = s.map_tables()
    accepted, quarantined = s.gate(extracted, mapped)
    assert s.verdict_gate(extracted, accepted, quarantined) == (
        False, 'REJECTED: "2026-13-01" is not a real date. 5 of 6 triples kept.')
    two = quarantined + [(s.CN.x, s.CN.startDate, Literal("x"), quarantined[0][3])]
    assert s.verdict_gate(Graph(), Graph(), two) == (False, "REJECTED: 2 of 0 triples break the shape; 0 kept.")


def test_ep06_metric_and_match_verdicts():
    s = load_step("ep06_real_data")
    assert s.verdict_metric([1, 3, 2], 2) == (True, "Three reports said 1, 3 and 2; one definition says 2.")
    assert s.verdict_metric([2, 2, 2], 2) == (True, "The reports already agree on 2; now it is written down once.")
    # rows: (score, name, source, customer, matched)
    ok = lambda name: (0.9, name, "crm", "Acme Health", True)  # noqa: E731
    doubt = lambda name: (0.5, name, "news", "Acme Health", False)  # noqa: E731
    assert s.verdict_match([ok("a"), ok("b"), ok("c"), doubt("d"), doubt("e")]) == (
        None, "Three names matched Acme Health; two go to a person to review.")
    assert s.verdict_match([ok("a"), doubt("d")]) == (None, "One name matched Acme Health; one goes to a person to review.")
    assert s.verdict_match([ok("a"), ok("b")]) == (True, "Two names matched Acme Health; nobody needs to review.")
    assert s.verdict_match([doubt("d")]) == (None, "No name scored 0.80 or more; one goes to a person to review.")


# sections shown as terminal cards (not in a demo) still end on one verdict line
CARD_SECTIONS = {
    ("ep06_real_data", "semantic-layer"): "✓ Three reports said 1, 3 and 2; one definition says 2.",
    ("ep06_real_data", "match"): "→ Three names matched Acme Health; two go to a person to review.",
    ("ep09_design", "rule"): "✓ This rule has an owner, a written reason and a date.",
}


@pytest.mark.parametrize("step,slug", list(CARD_SECTIONS), ids=[f"{s}-{o}" for s, o in CARD_SECTIONS])
def test_card_section_prints_one_verdict(step, slug):
    lines = verdicts(run(step, slug))
    assert lines == [CARD_SECTIONS[(step, slug)]]
    assert len(lines[0][2:].split()) <= 14, lines[0]
    assert lines[0] + "\n" in (LAB / step / "expected.txt").read_text(encoding="utf-8")


def test_ep09_rule_verdict_needs_owner_reason_and_date():
    s = load_step("ep09_design")
    card = {"owner": "x", "why": "y", "since": "2026-10-31"}
    assert s.verdict_rule(card) == (True, "This rule has an owner, a written reason and a date.")
    assert s.verdict_rule(dict(card, owner=None)) == (False, "No owner: nobody can explain or challenge this rule.")
    assert s.verdict_rule({"owner": None, "why": None, "since": "d"}) == (
        False, "No owner and written reason: nobody can explain or challenge this rule.")


def test_ep07_verdicts_read_the_answer():
    s = load_step("ep07_context_for_ai")
    rows = s.retrieve()
    assert s.verdict_facts(rows) == (None, "From the graph: Emma and Daniel worked on it; Emma's training is due.")
    done = [dict(r, training="trained") for r in rows]
    assert s.verdict_facts(done) == (None, "From the graph: Emma and Daniel worked on it; nobody's training is due.")
    assert s.verdict_without("I can't answer that.", rows) == (None, "No context: the model cannot answer.")
    assert s.verdict_without("I can’t answer that.", rows) == (None, "No context: the model cannot answer.")
    assert s.verdict_without("It was Priya and Sam.", rows) == (None, "No context: it names none of the real people.")
    assert s.verdict_without("Emma did it.", rows) == (None, "No context, yet it names Emma: a guess, not a source.")
    assert s.verdict_with("Emma Clarke and Daniel Brooks.", rows) == (None, "With the facts, it names Emma and Daniel.")
    assert s.verdict_with("No idea.", rows) == (None, "With the facts, it still names nobody.")


def test_ep07_search_verdict_checks_people_and_training():
    s = load_step("ep07_context_for_ai")
    rows = s.retrieve()
    top = [(5.3, "a.txt", "x")] * 3
    lead = "Search found three similar chunks; "
    recorded = (LAB / "data" / "llm" / "ep07_search.txt").read_text(encoding="utf-8")
    assert s.verdict_search(recorded, top, rows) == (None, lead + "it gets Emma's training, not who built it.")
    # the graph's answer, through the same check: Emma built it and needs training; Daniel is left out
    graph = (LAB / "data" / "llm" / "ep07_with.txt").read_text(encoding="utf-8")
    assert s.verdict_search(graph, top, rows) == (None, lead + "it gets Emma's training but misses Daniel.")
    both = "Emma Clarke led Claims AI and Daniel Brooks reviewed it. Emma still needs HIPAA training."
    assert s.verdict_search(both, top, rows) == (None, lead + "it names Emma and Daniel and gets Emma's training.")
    assert s.verdict_search("Emma led it and Daniel reviewed it.", top, rows) == (
        None, lead + "it names Emma and Daniel but not who needs training.")
    assert s.verdict_search("Emma led it. Daniel needs HIPAA training.", top, rows) == (
        None, lead + "it misses Daniel and who needs training.")
    assert s.verdict_search("Emma led it. Her HIPAA training is done.", top[:1], rows) == (
        None, "Search found one similar chunk; it misses Daniel and who needs training.")
    done = [dict(r, training="trained") for r in rows]
    assert s.verdict_search("Emma and Daniel built it.", top, done) == (
        None, lead + "it names Emma and Daniel and gets the training right.")


def test_ep07_agent_verdict_counts_the_tool_calls():
    s = load_step("ep07_context_for_ai")
    rows = s.retrieve()
    one = [("people_on_projects", {"product": "Cirrus AI", "industry": "healthcare"}, "Emma Clarke ...")]
    assert s.verdict_agent(one, "Emma Clarke.", rows) == (None, "One tool call through MCP; the answer names Emma.")
    three = one * 3
    assert s.verdict_agent(three, "Emma and Daniel.", rows) == (
        None, "Three tool calls through MCP; the answer names Emma and Daniel.")
    assert s.verdict_agent(one, "John Doe needs it.", rows) == (
        None, "One tool call through MCP; yet the answer names nobody.")
    assert s.verdict_agent([], "Emma.", rows) == (None, "No tool calls: the model answered without the graph.")


def test_ep08_verdicts():
    s = load_step("ep08_production")
    assert s.verdict_ci(True, 4, 4) == (True, "Passed: the data fits every shape, and all four questions get answers.")
    assert s.verdict_ci(False, 3, 4) == (False, "Failed: a shape check fails, and one question gets no answer.")
    assert s.verdict_ci(True, 3, 4) == (False, "Failed: one question gets no answer.")
    assert s.verdict_diff(1, 5) == (None, "Six changes in meaning: one fact removed, five added.")
    assert s.verdict_diff(0, 0) == (None, "No change in meaning.")
    assert s.verdict_taxonomy(3, "Cirrus AI", "AI services") == (
        None, "Three names, one service: Cirrus AI is a kind of AI services.")
