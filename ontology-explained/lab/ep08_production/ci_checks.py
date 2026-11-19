"""Ontology CI: the data must fit the shapes and answer every question."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pyshacl
from rdflib import Graph
from common.io import competency_questions, load_cloudnova, verdict
from ep08_production.step import SHAPES, ci_line, family, verdict_ci


def fits(data, shape_file):
    shapes = Graph().parse(SHAPES / shape_file, format="turtle")
    ok, _, _ = pyshacl.validate(data, shacl_graph=shapes,
                                inference="none", advanced=False)
    return ok


def main():
    cloudnova = load_cloudnova(labs=True)
    shacl = (fits(family(), "person-shape.ttl")
             and fits(cloudnova, "engagement-shape.ttl"))
    questions = [query for _id, _text, query in competency_questions()]
    answered = sum(1 for q in questions if len(cloudnova.query(q)) > 0)
    print(ci_line(shacl, answered, len(questions)))  # heading, ✓ or ✗
    verdict(*verdict_ci(shacl, answered, len(questions)))
    return shacl and answered == len(questions)


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)  # a failed check fails the build
