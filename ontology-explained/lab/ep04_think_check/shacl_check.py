"""Check a spreadsheet row against the person shape, with SHACL."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyshacl
from rdflib import Graph
from common.io import verdict
from ep04_think_check.step import DAD, SHAPES, dad_row, heading, report_rows
from ep04_think_check.step import verdict_row


def check(data):  # (conforms, one line per value the shape rejects)
    shapes = Graph().parse(SHAPES, format="turtle")
    conforms, report, _ = pyshacl.validate(
        data, shacl_graph=shapes, inference="none", advanced=False)
    return conforms, report_rows(report)


def main(csv_file=DAD):
    row = dad_row(csv_file)  # Rose C.'s row, her birth date as written
    conforms, rows = check(row)
    print(heading(csv_file, row))
    print(f"conforms: {conforms}")
    for line in rows:
        print(f"violation: {line}")
    verdict(*verdict_row(csv_file, row, conforms, rows))


if __name__ == "__main__":
    main(*sys.argv[1:])  # another CSV file, or Dad's by default
