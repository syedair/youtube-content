"""Episode 3: meaning. The ontology lets the computer work out facts nobody wrote.

Then the trap: a typo makes RDFS infer a wrong fact without a word, and OWL's "never" (disjointWith) catches it.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rdflib import OWL, RDF, RDFS, Graph  # noqa: E402

from common.carter import ONTOLOGY, bind, merged  # noqa: E402
from common.io import name_list, number, sections, verdict  # noqa: E402
from common.ns import CN, short  # noqa: E402

HERE = Path(__file__).resolve().parent
CLOUDNOVA_ONTOLOGY = HERE.parent / "data" / "ontology" / "cloudnova.ttl"
TYPED = HERE / "works-on.ttl"  # Globex Bank as the CRM has it, plus two facts someone typed in


def reason(g, s, cls):
    why = []
    if any(g.value(p, RDFS.range) == cls for _, p in g.subject_predicates(s)):
        why.append("range")
    if any(g.value(p, RDFS.domain) == cls for p in g.predicates(s)):
        why.append("domain")
    return " and ".join(why)


def inferred():
    from ep03_meaning import reasoner  # reasoner.py imports from this file, so import it here
    data = merged()
    onto = bind(Graph()).parse(ONTOLOGY, format="turtle")
    g = bind(Graph())
    g += data
    g += onto
    before = bind(Graph())
    before += g
    reasoner.reason(g, owl=False)

    lines = []
    for s, p, o in set(g) - set(before):
        # Keep only meaningful news about our family; drop rdfs:Resource noise etc.
        if short(s) is None or p != RDF.type or short(o) is None:
            continue
        lines.append(f"{short(s)} a {short(o)} (inferred from {reason(before, s, o)})")
    return len(data), sorted(lines)


# ---- the Globex Bank typo (Cloudnova)

def cn(term) -> str:
    """cn: prefixed form of a Cloudnova IRI (anything else as it is)."""
    s = str(term)
    return "cn:" + s[len(CN):] if s.startswith(str(CN)) else s


def label(term) -> str:
    """cn:globex-bank -> Globex Bank."""
    return cn(term)[3:].replace("-", " ").title()


def article(cls) -> str:
    word = cn(cls)[3:]
    return ("an " if word[:1] in "AEIOU" else "a ") + word


def cloudnova(owl: bool) -> Graph:
    """The typed facts plus the Cloudnova ontology: its RDFS lines only, or all of it (OWL too)."""
    g = Graph()
    g.bind("cn", CN)
    g.parse(TYPED, format="turtle")
    onto = Graph().parse(CLOUDNOVA_ONTOLOGY, format="turtle")
    for t in onto:
        if owl or not any(str(x).startswith(str(OWL)) for x in t):
            g.add(t)
    return g


def verdict_trap(n_errors: int, odd: list[str]):
    """odd: things the reasoner made an Employee although they are written down as something else."""
    if n_errors:
        return True, f"RDFS raised {number(n_errors)} errors."
    if odd:
        return False, f"No error, no warning: RDFS made {name_list(odd)} an Employee."
    return None, "RDFS only added types, and nothing looks out of place."


def report_trap(g: Graph, written: Graph, found: list[str]):
    """Print the trap section from an RDFS-reasoned graph g, the graph as written, and the reasoner's errors
    (found); rdfs_infer.py, runnable by itself, does the reasoning."""
    prop = CN.worksOn
    dom, rng = g.value(prop, RDFS.domain), g.value(prop, RDFS.range)
    print(f"== trap: RDFS reads the typed facts ({TYPED.parent.name}/{TYPED.name}) ==")
    print(f"rule: {cn(prop)} domain {cn(dom)}, range {cn(rng)}")
    types = set(written.subject_objects(RDF.type))
    lines, odd = [], []
    for s, o in sorted(set(g.subject_objects(prop))):
        for thing, cls, why in ((s, dom, "domain"), (o, rng, "range")):
            if (thing, cls) not in types:
                lines.append(f"{cn(thing)} a {cn(cls)} (inferred from {why})")
            # written down as something else (a Customer), and now an Employee too
            if cls == dom and any(t != cls for x, t in types if x == thing):
                odd.append(label(thing))
    for line in sorted(set(lines)):
        print(line)
    print(f"errors: {len(found)}")
    verdict(*verdict_trap(len(found), sorted(set(odd))))


def chain(g: Graph, written: Graph, x, target) -> list[str]:
    """Why x is a target: a written type, or a property's domain, then subClassOf steps up to target."""
    starts = [(t, f"{cn(x)} a {cn(t)}", "(written down)") for t in sorted(g.objects(x, RDF.type))
              if (x, RDF.type, t) in written]
    for p, o in sorted(g.predicate_objects(x)):
        d = g.value(p, RDFS.domain)
        if d is not None:
            starts.append((d, f"{cn(x)} {cn(p)} {cn(o)}", f"=> a {cn(d)} (domain)"))
    for t, fact, why in starts:
        path, cur = [], t
        while cur != target:
            nxt = g.value(cur, RDFS.subClassOf)
            if nxt is None:
                break
            path.append((cur, nxt))
            cur = nxt
        if cur == target:
            rows = [(fact, why)] + [(f"{cn(a)} subClassOf {cn(b)}", f"=> a {cn(b)}") for a, b in path]
            width = max(len(f) for f, _ in rows)
            return [f"  {f.ljust(width)}  {w}" for f, w in rows]
    return [f"  (no chain found to {cn(target)})"]


def verdict_clash(clashes: list[tuple]):
    """clashes: (thing, class, class) for each thing found in two disjoint classes."""
    if not clashes:
        return True, "CONSISTENT: nothing is in two classes that never overlap."
    x, c1, c2 = clashes[0]
    return False, f"CONTRADICTION: {label(x)} can't be {article(c1)} and {article(c2)}."


def report_clash(g: Graph, written: Graph, found: list[str]):
    """Print the clash section from a reasoned graph g, the graph as written, and the reasoner's errors (found);
    reasoner.py, runnable by itself, does the reasoning."""
    pairs = sorted(written.subject_objects(OWL.disjointWith))
    rules = ", ".join(f"{cn(a)} disjointWith {cn(b)}" for a, b in pairs) or "no disjointWith rule"
    print(f"== clash: OWL adds {rules} ==")
    clashes = []
    for msg in found:
        m = re.fullmatch(r"Disjoint classes (\S+) and (\S+) have a common individual (\S+)", msg)
        if m:
            c1, c2, x = (CN[v[len(CN):]] if v.startswith(str(CN)) else v for v in m.groups())
            clashes.append((x, c1, c2))
    for x, c1, c2 in clashes:
        for c in (c1, c2):
            print(f"why {cn(x)} is {article(c)}:")
            for line in chain(g, written, x, c):
                print(line)
    for msg in found:
        print("reasoner: " + re.sub(re.escape(str(CN)), "cn:", msg))
    verdict(*verdict_clash(clashes))


def main():
    only = sections(["inferred", "trap", "clash"])
    want = lambda name: only is None or name in only  # noqa: E731
    if want("inferred"):
        n, lines = inferred()
        if only is None:
            print(f"Written down: {n} facts. Plus the ontology's rules.\n")
        print("== inferred by RDFS (nobody wrote these) ==")
        for line in lines:
            print(line)
        print(f"\ninferred facts: {len(lines)}\n")
    # the trap and the clash are their own short files, runnable by themselves (they import from this file):
    # rdfs_infer.py (RDFS only) and reasoner.py (OWL)
    from ep03_meaning import rdfs_infer, reasoner

    if want("trap"):
        rdfs_infer.main()
        print()
    if want("clash"):
        reasoner.main()
        print()


if __name__ == "__main__":
    main()
