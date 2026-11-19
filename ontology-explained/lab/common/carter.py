"""Load the Carter family CSV files into rdflib graphs (shared by ep02 and ep03)."""
import csv
from pathlib import Path

from rdflib import RDF, XSD, Graph, Literal

from common.ns import FAM

DATA = Path(__file__).resolve().parent.parent / "data" / "carter"
ONTOLOGY = Path(__file__).resolve().parent.parent / "data" / "ontology" / "family.ttl"
LITERALS = {"name", "birthName", "birthDate"}


def bind(g: Graph) -> Graph:
    g.bind("fam", FAM)
    g.bind("xsd", XSD)
    return g


def load_csv(name: str) -> Graph:
    """One CSV of subject,predicate,object rows -> a graph. IRIs come from fam:."""
    g = bind(Graph())
    with open(DATA / name, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            s, p, o = FAM[row["subject"]], row["predicate"], row["object"]
            if p == "a":
                g.add((s, RDF.type, FAM[o]))
            elif p == "birthDate":
                g.add((s, FAM[p], Literal(o, datatype=XSD.date)))
            elif p in LITERALS:
                g.add((s, FAM[p], Literal(o)))
            else:
                g.add((s, FAM[p], FAM[o]))
    return g


def merged() -> Graph:
    """Both family files added together: same IRIs, so the facts just stack."""
    g = bind(Graph())
    for name in ("david-tree.csv", "maya-photos.csv"):
        g += load_csv(name)
    return g
