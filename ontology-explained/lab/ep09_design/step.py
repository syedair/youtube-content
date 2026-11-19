"""Episode 9: design from questions. Write the competency questions first, then check each has an answer.

Then one business rule, with the owner, the reason and the date written next to it."""
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pyshacl  # noqa: E402
from rdflib import DCTERMS, RDF, RDFS, SH, SKOS, Graph  # noqa: E402

from common.io import LAB_ROOT, competency_questions, load_cloudnova, name_list, sections, verdict  # noqa: E402

logging.disable(logging.CRITICAL)

RULE = LAB_ROOT / "data" / "shapes" / "hipaa-training-rule.ttl"


def terms(query: str) -> str:
    """The cn: classes and properties a question needs: what the ontology must name."""
    return ", ".join(sorted(set(re.findall(r"\bcn:[A-Za-z]+", query))))


def rule_card(shapes: Graph) -> dict:
    """The rule's own record: what it says, who owns it, why it exists, since when (read from the shape)."""
    rule = next(shapes.subjects(RDF.type, SH.NodeShape))
    get = lambda p: shapes.value(rule, p)  # noqa: E731
    return {"label": get(RDFS.label), "rule": get(SKOS.definition), "owner": get(DCTERMS.creator),
            "why": get(RDFS.comment), "since": get(DCTERMS.created)}


def flagged(data: Graph, shapes: Graph) -> list[str]:
    """Who the rule flags in the data (SHACL validation, focus nodes by name)."""
    _, report, _ = pyshacl.validate(data, shacl_graph=shapes, inference="none", advanced=False)
    nodes = {report.value(r, SH.focusNode) for r in report.subjects(RDF.type, SH.ValidationResult)}
    return sorted(str(data.value(n, RDFS.label)) for n in nodes)


def verdict_rule(card: dict):
    """A rule anyone can question has an owner, a written reason and a date."""
    missing = [name for key, name in (("owner", "owner"), ("why", "written reason"), ("since", "date"))
               if not card[key]]
    if missing:
        return False, f"No {name_list(missing)}: nobody can explain or challenge this rule."
    return True, "This rule has an owner, a written reason and a date."


def main():
    cqs = competency_questions()
    only = sections([cq.lower() for cq, _q, _query in cqs] + ["rule"])
    g = load_cloudnova(labs=True)
    if only is None:
        print("Start from questions. Each one is a SPARQL query in competency-questions.rq.")
        print()
    for cq, question, query in cqs:
        if only is not None and cq.lower() not in only:
            continue
        answers = sorted(str(row[0]) for row in g.query(query))
        print(f"== {cq}: {question} ==")
        print(f"the ontology must name: {terms(query)}")
        print("answer:")
        for a in answers or ["(no answer)"]:
            print(f"  {a}")
        print()
    if only is None or "rule" in only:
        shapes = Graph().parse(RULE, format="turtle")
        card = rule_card(shapes)
        print(f"== rule: {card['label']}, and who decided it ({RULE.relative_to(LAB_ROOT)}) ==")
        for key in ("rule", "owner", "why", "since"):
            print(f"{key + ':':7}{card[key] or '(not written down)'}")
        print(f"{'flags:':7}{name_list(flagged(g, shapes))}")
        verdict(*verdict_rule(card))


if __name__ == "__main__":
    main()
