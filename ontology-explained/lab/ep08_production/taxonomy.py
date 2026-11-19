"""Read the SKOS taxonomy: what Cirrus AI is a kind of, and its other names."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdflib import SKOS, Graph
from common.io import verdict
from common.ns import CN
from ep08_production.step import HERE, verdict_taxonomy


def main():
    t = Graph().parse(HERE / "skos-services.ttl", format="turtle")
    nm = t.namespace_manager
    term = CN["cirrus-ai"]
    parent = t.value(term, SKOS.broader)  # kind-of, and nothing else
    pref = t.value(term, SKOS.prefLabel)
    alt_labels = sorted(t.objects(term, SKOS.altLabel))  # its other names
    alts = ", ".join(sorted(a.n3() for a in alt_labels))
    print("== taxonomy: kind-of and nothing else (skos-services.ttl) ==")
    print(f"{term.n3(nm)} is a kind of {parent.n3(nm)}  "
          f"(prefLabel {pref.n3()}; altLabel {alts})")
    parent_label = str(t.value(parent, SKOS.prefLabel))
    verdict(*verdict_taxonomy(1 + len(alt_labels), str(pref), parent_label))


if __name__ == "__main__":
    main()
