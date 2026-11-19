"""RDFS only: domain and range add types to the typed facts, never errors."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rdflib import Graph
from ep03_meaning.reasoner import errors, reason
from ep03_meaning.step import cloudnova, report_trap


def main():
    graph = cloudnova(owl=False)  # the typed facts, plus the RDFS lines only
    written = Graph() + graph  # a copy of what was written down
    reason(graph, owl=False)  # RDFS: worksOn's domain makes an Employee
    report_trap(graph, written, errors(graph))  # what it added, the verdict


if __name__ == "__main__":
    main()
