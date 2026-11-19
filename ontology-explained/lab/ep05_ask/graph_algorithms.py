"""Graph algorithms on Cloudnova: who is most central, and a short path."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import networkx as nx
from rdflib import RDF, RDFS, URIRef
from common.io import load_cloudnova, verdict
from ep05_ask.step import verdict_algorithms


def main():
    rdf = load_cloudnova()
    net = nx.Graph()  # each link between two things becomes an edge
    for s, p, o in rdf:
        if p != RDF.type and isinstance(o, URIRef):
            net.add_edge(str(rdf.value(s, RDFS.label)),
                         str(rdf.value(o, RDFS.label)))
    print("== graph algorithms on CloudNova ==")
    print(f"nodes: {net.number_of_nodes()}, edges: {net.number_of_edges()}")
    scores = nx.betweenness_centrality(net)
    top = max(sorted(scores), key=scores.get)  # a tie goes to A before Z
    print(f"most central: {top}")
    path = nx.shortest_path(net, "Emma Clarke", "Globex Bank")
    print("shortest path Emma Clarke → Globex Bank: " + " → ".join(path))
    verdict(*verdict_algorithms(top, path))


if __name__ == "__main__":
    main()
