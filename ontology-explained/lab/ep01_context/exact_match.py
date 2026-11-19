"""The naive join: two names link only if they are spelled the same."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from ep01_context.step import load, verdict_join


def exact_pairs(records):
    pairs = []
    for i, (source, name) in enumerate(records):
        for other_source, other_name in records[i + 1:]:
            if name == other_name:
                pairs.append((source, other_source))
    return pairs


def main():
    records = [(source, name) for source, _field, name in load()]
    pairs = exact_pairs(records)
    print("== naive join: exact string match on name ==")
    for a, b in sorted(pairs):
        print(f"{a} = {b}")
    print(f"exact-match pairs: {len(pairs)}")
    verdict(*verdict_join(len(records), len(pairs)))
    print("\nSame person? You know it. The computer doesn't.")


if __name__ == "__main__":
    main()
