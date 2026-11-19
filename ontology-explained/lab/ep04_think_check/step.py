"""Episode 4: think and check. Reason over the data, validate it with SHACL, apply a rule."""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import owlrl  # noqa: E402
from rdflib import RDF, SH, XSD, Graph, Literal  # noqa: E402

from common.carter import DATA, ONTOLOGY, bind, load_csv, merged  # noqa: E402
from common.io import sections, show  # noqa: E402
from common.ns import FAM, short  # noqa: E402

LAB = Path(__file__).resolve().parent.parent
SHAPES = LAB / "data" / "shapes" / "person-shape.ttl"
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

GRANDPARENT_RULE = """\
PREFIX fam: <https://family.example/id/>
CONSTRUCT { ?gp fam:grandparentOf ?gc }
WHERE     { ?gp fam:hasChild ?p .
            ?p  fam:hasChild ?gc . }"""


def family() -> Graph:
    """Merged family files + Rose's marriage to Tom + the ontology."""
    g = bind(Graph())
    g += merged()
    g += load_csv("marriage.csv")
    g += bind(Graph()).parse(ONTOLOGY, format="turtle")
    return g


def reason(quiet: bool = False):
    g = family()
    before = bind(Graph())
    before += g
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    lines = []
    for s, p, o in set(g) - set(before):
        # Keep meaningful news between family members; drop axiomatic OWL noise.
        if short(s) and short(p) and short(o) and p != RDF.type:
            lines.append(f"{short(s)} {short(p)} {short(o)} (inferred)")
    if not quiet:
        show("reason: what the computer works out", lines)
    return g


DAD = "data/carter/dad-spreadsheet.csv"  # Dad's row as he typed it (lab-relative)
FIXED = "data/carter/dad-spreadsheet-fixed.csv"  # the same row, the date written as a real date


def csv_path(name: str) -> Path:
    """A bare file name is in data/carter; a path is relative to the lab folder."""
    p = Path(name)
    return p if p.is_absolute() else DATA / p if len(p.parts) == 1 else LAB / p


def dad_row(name: str = DAD) -> Graph:
    """Dad's spreadsheet row. A born value written as a real date (YYYY-MM-DD) becomes an xsd:date;
    anything else (03/04/31) stays a plain string."""
    g = bind(Graph())
    with open(csv_path(name), encoding="utf-8", newline="") as f:
        row = next(csv.DictReader(f))
    rose = FAM["rose-carter"]
    born = row["born"]
    g.add((rose, RDF.type, FAM.Person))
    g.add((rose, FAM.birthDate, Literal(born, datatype=XSD.date) if ISO_DATE.fullmatch(born) else Literal(born)))
    return g


def report_rows(report: Graph) -> list[str]:
    """A SHACL validation report as one sorted line per violation: node, property, value -> message."""
    rows = []
    for r in report.subjects(RDF.type, SH.ValidationResult):
        focus = report.value(r, SH.focusNode)
        path = report.value(r, SH.resultPath)
        value = report.value(r, SH.value)
        msg = report.value(r, SH.resultMessage)
        rows.append(f"{short(focus)} {short(path)} {value.n3()} -> {msg}")
    return sorted(rows)


def violations(data: Graph):
    """Validate against the person shape (shacl_check.py, runnable by itself); return (conforms, rows)."""
    from ep04_think_check import shacl_check  # it imports from this file, so import it here

    return shacl_check.check(data)


def verdict_check(conforms: bool, rows: list[str]):
    """What the check means: the rejected value and the example the rule's message gives."""
    if conforms:
        return True, "ACCEPTED: the row fits the rule."
    m = re.search(r' (".*?") -> .*?such as (\S+)', rows[0])
    value, example = m.groups() if m else (rows[0].split(" -> ")[0].split()[-1], None)
    want = f"The rule wants {example}." if example else "It breaks the rule."
    return False, f"REJECTED: {value} is not a real date. {want}"


def verdict_fix(conforms: bool, born: Literal):
    if conforms:
        return True, f"ACCEPTED: the birth date is now a real date, {born}."
    return False, f'REJECTED: "{born}" still breaks the rule.'


def heading(name: str, row: Graph) -> str:
    """The check's heading: Dad's row as he typed it, or the row after the fix, with its birth date."""
    if csv_path(name) == csv_path(DAD):
        return "== check: Dad's spreadsheet row against the person shape =="
    return f"== check: after the fix {row.value(FAM['rose-carter'], FAM.birthDate).n3(row.namespace_manager)} =="


def verdict_row(name: str, row: Graph, conforms: bool, rows: list[str]):
    """Dad's row: what was rejected (verdict_check); a fixed row: is its date real now (verdict_fix)."""
    if csv_path(name) == csv_path(DAD):
        return verdict_check(conforms, rows)
    return verdict_fix(conforms, row.value(FAM["rose-carter"], FAM.birthDate))


def rule(g: Graph):
    print("== rule: grandparent ==")
    print(GRANDPARENT_RULE)
    print()
    made = [f"{short(s)} {short(p)} {short(o)}" for s, p, o in g.query(GRANDPARENT_RULE)]
    show("rule result", made)


def main():
    only = sections(["reason", "check", "fix", "rule"])
    want = lambda name: only is None or name in only  # noqa: E731
    g = reason(quiet=not want("reason"))
    # the check is its own short file, runnable by itself (it imports from this file): shacl_check.py, on Dad's
    # row, then on the fixed row (data/carter/dad-spreadsheet-fixed.csv)
    from ep04_think_check import shacl_check

    if want("check"):
        shacl_check.main()
        print()
    if want("fix"):
        shacl_check.main(FIXED)
        print()
    if want("rule"):
        rule(g)


if __name__ == "__main__":
    main()
