"""One marriage, two ways: a bare RDF triple, and an edge that has details."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from ep05_ask.step import MARRIAGE, bare_triple, marriage, value
from ep05_ask.step import verdict_property_graph


def main():
    rdf, triple, edges = marriage()  # the same CSV row, read two ways
    bare = bare_triple(rdf, triple)
    print("== property graph: Rose and Tom's marriage "
          f"(data/carter/{MARRIAGE.name}) ==")
    print(f"RDF triple:      {bare}")
    most = 0
    for a, b, label, props in edges.edges(keys=True, data=True):
        inside = ", ".join(f"{k}: {value(v)}" for k, v in props.items())
        print(f"property graph:  ({a})-[:{label} {{{inside}}}]->({b})")
        notes = " ; ".join(f"fam:{k} {value(v)}" for k, v in props.items())
        print(f"RDF 1.2 notes:   {bare[:-2]} {{| {notes} |}} .")
        most = max(most, len(props))  # details on the link
    verdict(*verdict_property_graph(most))


if __name__ == "__main__":
    main()
