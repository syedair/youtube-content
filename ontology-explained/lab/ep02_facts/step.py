"""Episode 2: facts. Two family files, one Rose, nine triples."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rdflib import RDF, Graph  # noqa: E402

from common.carter import load_csv, merged  # noqa: E402
from common.io import number, out_dir, sections  # noqa: E402
from common.ns import FAM, short  # noqa: E402

PREFIXES = (
    "@prefix fam: <https://family.example/id/> .\n"
    "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n"
)
ORDER = ["name", "birthName", "bornIn", "birthDate", "hasChild"]


def obj(o):
    if short(o):
        return short(o)
    lit = f'"{o}"'
    return lit + "^^xsd:date" if o.datatype else lit


def turtle(g: Graph) -> str:
    """Hand-laid-out Turtle (rdflib's own layout varies), same style as the deck."""
    lines = []
    for s in sorted(set(g.subjects()), key=lambda s: (-len(list(g.predicate_objects(s))), str(s))):
        parts = []
        types = sorted(g.objects(s, RDF.type))
        if types:
            parts.append("a " + ", ".join(short(t) for t in types))
        for p in ORDER:
            vals = sorted(g.objects(s, FAM[p]), key=str)
            if vals:
                parts.append(f"fam:{p} " + " , ".join(obj(v) for v in vals))
        lines.append(f"{short(s)} " + " ; ".join(parts) + " .")
    return "\n".join(lines) + "\n"


def ntriples(g: Graph) -> str:
    return "".join(sorted(l + "\n" for l in g.serialize(format="nt").splitlines() if l))


def canon(x):
    if isinstance(x, dict):
        return {k: canon(v) for k, v in sorted(x.items())}
    if isinstance(x, list):
        return sorted((canon(v) for v in x), key=lambda v: json.dumps(v, sort_keys=True))
    return x


def jsonld(g: Graph) -> str:
    ctx = {"fam": str(FAM), "xsd": "http://www.w3.org/2001/XMLSchema#"}
    data = json.loads(g.serialize(format="json-ld", context=ctx))
    return json.dumps(canon(data), indent=2, ensure_ascii=False) + "\n"


def children(g, who):
    return ", ".join(short(c) for c in sorted(g.objects(who, FAM.hasChild)))


def excerpt(g: Graph) -> Graph:
    """The deck's carter-family.ttl excerpt: Rose's description plus David's facts."""
    ex = Graph()
    ex.bind("fam", FAM)
    for who in (FAM["rose-carter"], FAM["david-carter"]):
        for t in g.triples((who, None, None)):
            ex.add(t)
    return ex


def verdict_formats(counts: list[int], n: int):
    """Each spelling read back: the same n facts every time, or not."""
    if all(c == n for c in counts):
        return True, f"Same {n} facts, three spellings: each reads back as the same graph."
    return False, f"A spelling lost facts on the way back: {', '.join(map(str, counts))} of {n}."


def verdict_merge(n_roses: int):
    """What the merge means: one Rose node, or the files did not merge."""
    if n_roses == 1:
        return True, "One Rose, not two: both files' facts now sit on one node."
    return False, f"{number(n_roses).capitalize()} Roses: the files did not merge."


def main():
    only = sections(["merge", "turtle", "n-triples", "json-ld"])
    dad, maya = load_csv("david-tree.csv"), load_csv("maya-photos.csv")
    if only is None:
        print("Two family files. Both call her fam:rose-carter.\n")
        print(f"david-tree.csv:   {len(dad)} facts")
        print(f"maya-photos.csv:  {len(maya)} facts\n")
    want = lambda name: only is None or name in only  # noqa: E731
    # each part is its own short file, runnable by itself: merge.py, formats.py (they import from this file)
    from ep02_facts import formats, merge

    if want("merge"):
        merge.main()
        print()
    shown = [name for name in ("turtle", "n-triples", "json-ld") if want(name)]
    if shown:
        formats.main(shown)
    g = merged()
    (out_dir() / "carter.ttl").write_text(PREFIXES + "\n" + turtle(g), encoding="utf-8")


if __name__ == "__main__":
    main()
