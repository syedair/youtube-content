"""Read the five sources: the name each one gives Grandma."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ep01_context.step import load


def main():
    print("== sources ==")
    for source, field, name in sorted(load()):  # one record per source
        print(f'{source:<20} {field:<15} "{name}"')


if __name__ == "__main__":
    main()
