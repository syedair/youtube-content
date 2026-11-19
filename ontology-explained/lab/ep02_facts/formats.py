"""One graph, three spellings: Turtle, N-Triples and JSON-LD."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdflib import Graph
from common.carter import merged
from common.io import verdict
from ep02_facts.step import PREFIXES, excerpt, jsonld, ntriples, turtle
from ep02_facts.step import verdict_formats


def main(show=("turtle", "n-triples", "json-ld")):
    facts = excerpt(merged())  # Rose's and David's facts
    counts = []
    for heading, fmt, text in [("turtle", "turtle", PREFIXES + turtle(facts)),
                               ("n-triples", "nt", ntriples(facts)),
                               ("json-ld", "json-ld", jsonld(facts))]:
        back = Graph().parse(data=text, format=fmt)  # read it back in
        counts.append(len(back) if set(back) == set(facts) else 0)
        if heading in show:
            print(f"== {heading} ==\n{text}")
    if "json-ld" in show:
        print(f"triple count (all formats): {len(facts)}")
        verdict(*verdict_formats(counts, len(facts)))


if __name__ == "__main__":
    main()
