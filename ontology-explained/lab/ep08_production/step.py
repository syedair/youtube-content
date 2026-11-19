"""Episode 8: ontology in production. CI checks, a version diff, provenance per source, a taxonomy."""
import csv
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rdflib import RDF, Dataset, Graph, Literal, URIRef  # noqa: E402

from common.carter import DATA, bind, load_csv  # noqa: E402
from common.io import competency_questions, load_cloudnova, number, sections  # noqa: E402, F401 (the tests use them from here)
from common.ns import FAM  # noqa: E402

logging.disable(logging.CRITICAL)

HERE = Path(__file__).resolve().parent
SHAPES = HERE.parent / "data" / "shapes"
SOURCE = "https://family.example/source/"


def pretty(term, nm) -> str:
    return "a" if term == RDF.type else term.n3(nm)


def verdict_ci(shacl: bool, answered: int, total: int):
    if shacl and answered == total:
        return True, f"Passed: the data fits every shape, and all {number(total)} questions get answers."
    problems = [] if shacl else ["a shape check fails"]
    missing = total - answered
    if missing:
        problems.append(f"{number(missing)} question{'s' if missing > 1 else ''} get{'' if missing > 1 else 's'} no answer")
    return False, "Failed: " + ", and ".join(problems) + "."


def verdict_diff(removed: int, added: int):
    if not removed + added:
        return None, "No change in meaning."
    return None, (f"{number(removed + added).capitalize()} changes in meaning: "
                  f"{number(removed)} fact{'s' if removed != 1 else ''} removed, {number(added)} added.")


def verdict_taxonomy(n_names: int, label: str, parent: str):
    return None, f"{number(n_names).capitalize()} names, one service: {label} is a kind of {parent}."


def family() -> Graph:
    """The two family files, merged (as in episode 2)."""
    g = bind(Graph())
    for name in ("david-tree.csv", "maya-photos.csv"):
        g += load_csv(name)
    return g


def ci_line(shacl: bool, answered: int, total: int) -> str:
    """The CI section's heading and its one summary line, with ✓ or ✗ for each check."""
    mark = lambda ok: "✓" if ok else "✗"  # noqa: E731
    return ("== ontology CI: the checks a pipeline runs on every change ==\n"
            f"ontology CI: SHACL {mark(shacl)}  competency queries {answered}/{total} {mark(answered == total)}")


def provenance():
    """Each source file becomes its own named graph; ask which graph each fact came from."""
    ds = Dataset()
    ds.bind("fam", FAM)
    for name in ("david-tree.csv", "maya-photos.csv"):
        ds.graph(URIRef(SOURCE + name)).__iadd__(load_csv(name))
    # The census row says "R. Lee, 20, Toronto": Rose in 1951 (born 1931, Toronto), matched by hand in ep01.
    census = ds.graph(URIRef(SOURCE + "census-1951.csv"))
    with open(DATA / "census-1951.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            census.add((FAM["rose-carter"], FAM.birthName, Literal(row["birth_name"])))
    rows = ds.query("SELECT ?s ?p ?o ?g WHERE { GRAPH ?g { ?s ?p ?o } }")
    nm = ds.namespace_manager
    lines = sorted(
        f"{pretty(s, nm)} {pretty(p, nm)} {pretty(o, nm)}  ← source: {str(g)[len(SOURCE):]}"
        for s, p, o, g in rows
    )
    print("== provenance: one named graph per source ==")
    for line in lines:
        print(line)
    print()


def main():
    only = sections(["ci", "diff", "provenance", "taxonomy"])
    want = lambda name: only is None or name in only  # noqa: E731
    # the CI checks, the version diff and the taxonomy are their own short files, runnable by themselves (they
    # import from this file): ci_checks.py, diff_versions.py and taxonomy.py
    from ep08_production import ci_checks, diff_versions, taxonomy

    ok = True
    if want("ci"):
        ok = ci_checks.main()
        print()
    if want("diff"):
        diff_versions.main()
        print()
    if want("provenance"):
        provenance()
    if want("taxonomy"):
        taxonomy.main()
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
