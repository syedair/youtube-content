"""Run a reasoner over a graph, then read the errors it wrote down."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import owlrl
from rdflib import RDF, Graph, Namespace
from ep03_meaning.step import cloudnova, report_clash
# owlrl writes each problem it finds into the graph, in this namespace
ERR = Namespace("http://www.daml.org/2002/03/agents/agent-ont#")


def reason(graph, owl):
    rules = owlrl.OWLRL_Semantics if owl else owlrl.RDFS_Semantics
    owlrl.DeductiveClosure(rules).expand(graph)  # add every implied fact


def errors(graph):
    return sorted(str(m) for e in graph.subjects(RDF.type, ERR.ErrorMessage)
                  for m in graph.objects(e, ERR.error))


def main():
    graph = cloudnova(owl=True)  # the typed facts, plus the whole ontology
    written = Graph() + graph  # a copy of what was written down
    reason(graph, owl=True)
    report_clash(graph, written, errors(graph))  # why, and the verdict


if __name__ == "__main__":
    main()
