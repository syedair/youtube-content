"""Ask Wikidata's API who our Toronto is (saved answer; LAB_API=live)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from ep06_real_data.step import resolve_toronto, verdict_api


def main():
    triples, summary, label, country = resolve_toronto()  # Q172, Toronto
    print("== api: Wikidata resolves fam:toronto "
          "(Special:EntityData/Q172.json) ==")
    print(summary)
    nm = triples.namespace_manager
    for line in sorted(" ".join(x.n3(nm) for x in t) for t in triples):
        print(line)
    verdict(*verdict_api(label, country))


if __name__ == "__main__":
    main()
