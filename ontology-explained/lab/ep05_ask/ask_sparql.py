"""Ask the graph: run the SPARQL file, print the grandchildren it finds."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.carter import merged
from common.io import verdict
from ep05_ask.step import first_name, verdict_grandchildren

QUERY = Path(__file__).resolve().parent / "grandchildren.rq"


def grandchildren():
    graph = merged()  # the family files, as one graph
    rows = graph.query(QUERY.read_text(encoding="utf-8"))
    return sorted(first_name(gc) for (gc,) in rows)  # fam:leo-carter -> Leo


def main():
    names = grandchildren()
    print(f"== sparql: Rose's grandchildren (ep05_ask/{QUERY.name}) ==")
    print("Rose's grandchildren: " + ", ".join(names))
    verdict(*verdict_grandchildren(names))


if __name__ == "__main__":
    main()
