"""The merge: read each file's rows as facts, and add them together."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdflib import Graph
from common.carter import bind, load_csv
from common.io import verdict
from common.ns import FAM
from ep02_facts.step import children, excerpt, verdict_merge


def main():
    graph = bind(Graph())
    for name in ["david-tree.csv", "maya-photos.csv"]:
        graph += load_csv(name)  # same ID, same node: nothing to match
    roses = set(graph.subjects(FAM.name, None))  # only Rose has a name
    print("== merge: just add the facts together ==")
    print(f"fam:rose-carter children: {children(graph, FAM['rose-carter'])}")
    print(f"distinct Rose nodes after merge: {len(roses)}")
    print(f"merged graph: {len(graph)} triples")
    verdict(*verdict_merge(len(roses)))
    n = len(excerpt(graph))
    print(f"\nexcerpt: Rose and David, {n} of the {len(graph)} triples")


if __name__ == "__main__":
    main()
