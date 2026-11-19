"""The shape gate: keep the LLM's triples that fit, quarantine the rest."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyshacl
from ep06_real_data.step import SHAPES, extracted, map_tables, problems
from ep06_real_data.step import report_gate


def gate(new, known):
    _, report, _ = pyshacl.validate(known + new, shacl_graph=str(SHAPES),
                                    inference="none", advanced=False)
    broken = problems(report)  # (node, property, value) -> (rule, message)
    rejected = []
    for s, p, o in new:
        problem = broken.get((s, p, o)) or broken.get((s, p, None))
        if problem:
            rejected.append((s, p, o, problem))
    return rejected


def main(known=None):
    known = map_tables() if known is None else known  # the company's tables
    new = extracted()  # the triples the LLM wrote from the contract
    report_gate(new, gate(new, known))


if __name__ == "__main__":
    main()
