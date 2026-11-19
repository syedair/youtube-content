"""Small helpers so every step prints the same deterministic way."""
import os
import sys
from pathlib import Path
from typing import Iterable

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8")

LAB_ROOT = Path(__file__).resolve().parent.parent


def out_dir() -> Path:
    """lab/out/, created on first use. Generated files go here (git-ignored)."""
    d = LAB_ROOT / "out"
    d.mkdir(parents=True, exist_ok=True)
    return d


def sections(valid: Iterable[str], argv: list[str] | None = None) -> set[str] | None:
    """Parse `--only a,b` (or `--only a --only b`): the sections of a step to print.

    Returns None when the flag is absent (print everything). An unknown name prints
    the valid names to stderr and exits with status 2.
    """
    valid = list(valid)
    args = sys.argv[1:] if argv is None else argv
    chosen: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--only" and i + 1 < len(args):
            chosen += args[i + 1].split(",")
            i += 2
        elif a.startswith("--only="):
            chosen += a.split("=", 1)[1].split(",")
            i += 1
        else:
            print(f"unknown argument {a!r}; use --only <section>", file=sys.stderr)
            raise SystemExit(2)
    if not chosen:
        return None
    bad = [c for c in chosen if c not in valid]
    if bad:
        print(f"unknown section {bad[0]!r}; valid sections: {', '.join(valid)}", file=sys.stderr)
        raise SystemExit(2)
    return set(chosen)


def show(title: str, rows: Iterable[str]) -> None:
    """Print a titled block with rows in sorted order."""
    print(f"== {title} ==")
    for row in sorted(rows):
        print(row)
    print()


# ✓ green, ✗ red, → bold (ANSI, only on a terminal or with FORCE_COLOR; the goldens stay plain text)
_MARKS = {True: ("✓", "1;32"), False: ("✗", "1;31"), None: ("→", "1")}
_NUMBERS = "zero one two three four five six seven eight nine ten eleven twelve".split()


def colour() -> bool:
    """Colour on a terminal, or when FORCE_COLOR is set (not "0"); NO_COLOR always wins."""
    if os.environ.get("NO_COLOR"):
        return False
    force = os.environ.get("FORCE_COLOR", "")
    if force:
        return force != "0"
    return sys.stdout.isatty()


def verdict(ok: bool | None, text: str) -> None:
    """Print one plain-English line that says what a result means: ✓ (ok), ✗ (not ok) or → (neither)."""
    mark, code = _MARKS[ok]
    line = f"{mark} {text}"
    print(f"\033[{code}m{line}\033[0m" if colour() else line)


def number(n: int) -> str:
    """0-12 as a word (zero ... twelve), anything else as digits."""
    return _NUMBERS[n] if 0 <= n < len(_NUMBERS) else str(n)


def name_list(names: list[str]) -> str:
    """'nobody', 'A', 'A and B', 'A, B and C'."""
    names = list(names)
    if not names:
        return "nobody"
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def load_cloudnova(labs: bool = False):
    """CloudNova SQLite seed (plain SQL text) -> an rdflib Graph in the cn: namespace.

    labs=True also adds the patients and lab results (episodes 8 and 9 only).
    """
    import sqlite3

    from rdflib import RDF, RDFS, Graph, Literal

    from common.ns import CN

    db = sqlite3.connect(":memory:")
    db.executescript((LAB_ROOT / "data" / "cloudnova" / "cloudnova.sql").read_text(encoding="utf-8"))
    g = Graph()
    g.bind("cn", CN)
    g.bind("rdfs", RDFS)

    def node(table, cls, label_col="name"):
        for id_, label, *rest in db.execute(f"SELECT id, {label_col} FROM {table} ORDER BY id"):
            g.add((CN[id_], RDF.type, CN[cls]))
            g.add((CN[id_], RDFS.label, Literal(label)))

    node("person", "Person")
    node("customer", "Customer")
    node("product", "Product")
    node("engagement", "Engagement")
    for id_, role, training in db.execute("SELECT id, role, hipaa_training FROM person"):
        g.add((CN[id_], CN.role, Literal(role)))
        g.add((CN[id_], CN.hipaaTraining, Literal(training)))
    for id_, industry in db.execute("SELECT id, industry FROM customer"):
        g.add((CN[id_], CN.industry, Literal(industry)))
    for id_, cust, prod, lead, rev in db.execute(
        "SELECT id, customer_id, product_id, lead_id, reviewer_id FROM engagement"
    ):
        g.add((CN[id_], CN.forCustomer, CN[cust]))
        g.add((CN[id_], CN.uses, CN[prod]))
        if lead:
            g.add((CN[id_], CN.hasLead, CN[lead]))
        if rev:
            g.add((CN[id_], CN.hasReviewer, CN[rev]))
    if labs:
        node("patient", "Patient")
        node("lab_result", "LabResult")
        for id_, patient, loinc in db.execute("SELECT id, patient_id, loinc FROM lab_result ORDER BY id"):
            g.add((CN[id_], CN.forPatient, CN[patient]))
            if loinc:
                g.add((CN[id_], CN.loincCode, Literal(loinc)))
    db.close()
    return g


def competency_questions() -> list[tuple[str, str, str]]:
    """The competency questions, one source of truth: (id, question, sparql).

    Read from ep09_design/competency-questions.rq. Each block starts with a
    line like `# CQ1: <the question>` followed by its SPARQL query.
    """
    import re

    text = (LAB_ROOT / "ep09_design" / "competency-questions.rq").read_text(encoding="utf-8")
    parts = re.split(r"^# (CQ\d+): (.*)$", text, flags=re.M)
    return [(parts[i], parts[i + 1].strip(), parts[i + 2].strip()) for i in range(1, len(parts), 3)]
