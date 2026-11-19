"""Episode 5: asking the graph. A SPARQL question, a link that carries details, then graph algorithms on CloudNova."""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import networkx as nx  # noqa: E402

from common.carter import DATA, bind, load_csv  # noqa: E402
from common.io import load_cloudnova, name_list, number, sections  # noqa: E402, F401 (the tests use load_cloudnova from here)
from common.ns import FAM  # noqa: E402

# The question is a SPARQL file, grandchildren.rq; ask_sparql.py runs it (the demo shows both with `cat`).


def first_name(person) -> str:
    """fam:leo-carter -> Leo."""
    return str(person)[len(FAM):].split("-")[0].capitalize()


def verdict_grandchildren(names: list[str]):
    return None, f"Rose has {number(len(names))} grandchildren: {name_list(names)}."


def verdict_algorithms(top: str, path: list[str]):
    """Who is most central, and how many hops the shortest path takes."""
    return None, (f"{top} sits on the most paths; {path[0].split()[0]} is {number(len(path) - 1)} hops "
                  f"from {path[-1]}.")


MARRIAGE = DATA / "marriage.csv"  # subject,predicate,object, then the details of the link: since,place,source
TRIPLE = ("subject", "predicate", "object")


def marriage():
    """Rose and Tom's marriage, read two ways from data/carter/marriage.csv.

    RDF (common.carter.load_csv, as in episode 4) keeps subject, predicate, object: a bare triple.
    A property graph (networkx) keeps the row's other columns as properties on the edge itself.
    """
    rdf = load_csv(MARRIAGE.name)
    triple = next(t for t in rdf if t[1] == FAM.marriedTo)
    pg = nx.MultiDiGraph()
    with open(MARRIAGE, encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["predicate"] == "a":
                continue
            details = {k: int(v) if v.isdigit() else v for k, v in row.items() if k not in TRIPLE and v}
            label = re.sub(r"(?<!^)(?=[A-Z])", "_", row["predicate"]).upper()  # marriedTo -> MARRIED_TO
            pg.add_edge(row["subject"], row["object"], key=label, **details)
    return rdf, triple, pg


def value(v) -> str:
    return str(v) if isinstance(v, int) else '"' + v + '"'


def verdict_property_graph(n_details: int):
    if not n_details:
        return None, "A bare link: no details to carry."
    return None, f"One link, {number(n_details)} details: on the edge, or as RDF 1.2 notes."


def bare_triple(rdf, triple) -> str:
    """fam:rose-carter fam:marriedTo fam:tom-carter ."""
    nm = bind(rdf).namespace_manager
    return " ".join(t.n3(nm) for t in triple) + " ."


def main():
    only = sections(["sparql", "property-graph", "algorithms"])
    # each section is its own short file, runnable by itself (they import from this file): ask_sparql.py (the
    # query itself is in grandchildren.rq, so it is not printed again), property_graph.py, graph_algorithms.py
    from ep05_ask import ask_sparql, graph_algorithms, property_graph

    for slug, module in (("sparql", ask_sparql), ("property-graph", property_graph),
                         ("algorithms", graph_algorithms)):
        if only is None or slug in only:
            module.main()
            print()


if __name__ == "__main__":
    main()
