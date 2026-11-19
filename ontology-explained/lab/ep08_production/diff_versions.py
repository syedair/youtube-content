"""Diff two versions of the ontology: every fact removed (-) or added (+)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdflib import Graph
from rdflib.compare import graph_diff, to_isomorphic
from common.io import verdict
from ep08_production.step import HERE, pretty, verdict_diff


def main():
    v1 = Graph().parse(HERE / "family-v1.ttl", format="turtle")
    v2 = Graph().parse(HERE / "family-v2.ttl", format="turtle")
    # compare meaning, not text: blank nodes and line order don't count
    _, only1, only2 = graph_diff(to_isomorphic(v1), to_isomorphic(v2))
    nm = v2.namespace_manager
    lines = [(pretty(s, nm), pretty(p, nm), added, pretty(o, nm))
             for added, facts in ((False, only1), (True, only2))
             for s, p, o in facts]
    print("== version diff: family-v1.ttl -> family-v2.ttl ==")
    for s, p, added, o in sorted(lines):  # a removed fact before its new one
        print(f"{'+' if added else '-'} {s} {p} {o}")
    verdict(*verdict_diff(len(only1), len(only2)))


if __name__ == "__main__":
    main()
