"""The fix: look each name up in the who-is-who table, then count IDs."""
import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from ep01_context.exact_match import exact_pairs
from ep01_context.step import ACME, CLOUDNOVA, verdict_one_id


def read_table(path):
    """Each (system, name) in the table, with the one ID it means."""
    with open(path, encoding="utf-8", newline="") as f:
        return {(r["system"], r["name"]): r["id"] for r in csv.DictReader(f)}


def main():
    table = read_table(CLOUDNOVA / "who-is-who.csv")
    print("== one ID: look up Acme's five names in who-is-who.csv ==")
    print(f"before the table, exact-match pairs: {len(exact_pairs(ACME))}")
    ids = [table.get((system, name)) for system, name in ACME]
    for (system, name), rid in zip(ACME, ids):
        quoted = f'"{name}"'
        print(f"{system:<17} {quoted:<19} → {rid or '(no ID)'}")
    print(f"distinct customers: {len(set(ids) - {None})}")
    verdict(*verdict_one_id(len(ACME), set(ids), "customer", "one customer"))


if __name__ == "__main__":
    main()
