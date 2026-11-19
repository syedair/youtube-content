"""Retrieve the facts from the graph, by SPARQL: who worked on it, and HIPAA."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from ep07_context_for_ai.step import facts_block, retrieve, verdict_facts


def main(rows=None):
    rows = retrieve() if rows is None else rows  # the SPARQL query's rows
    print("== retrieved facts ==\n" + facts_block(rows))  # one line each
    verdict(*verdict_facts(rows))


if __name__ == "__main__":
    main()
