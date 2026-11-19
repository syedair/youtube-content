"""An MCP server: the Cloudnova graph as two tools an AI agent can call."""
import sys
from pathlib import Path
from typing import Annotated

from pydantic import Field

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mcp.server.mcpserver import MCPServer  # noqa: E402
from common.io import load_cloudnova  # noqa: E402

server = MCPServer("cloudnova-graph", log_level="ERROR")


@server.tool(structured_output=False)
def people_on_projects(
    product: Annotated[str, Field(description="A Cloudnova product name")],
    industry: Annotated[str, Field(description="The customers' industry, one word")],
) -> str:
    """Who worked on Cloudnova projects that use a product, for customers in an industry: name, job title, role."""
    rows = query(PEOPLE, product=product, industry=industry)
    return "\n".join(f"{r.name} ({r.title}): {r.relation} on {r.project} for {r.customer}" for r in rows) \
        or f"No projects use {product} for {industry} customers."


@server.tool(structured_output=False)
def hipaa_training() -> str:
    """The HIPAA training status of every person at Cloudnova, from the HR records: done, or due (still needs it)."""
    return "\n".join(f"{r.name}: HIPAA training {STATUS.get(str(r.training), r.training)}" for r in query(TRAINING))


# ---- the SPARQL behind the tools (the same graph and labels as step.py's retrieval)
PEOPLE = """\
PREFIX cn:   <https://data.cloudnova.example/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?name ?title ?relation ?project ?customer
WHERE { ?e a cn:Engagement ; cn:forCustomer ?c ; cn:uses ?p ; rdfs:label ?project .
        ?c cn:industry ?ind ; rdfs:label ?customer .
        ?p rdfs:label ?prod .
        FILTER (LCASE(STR(?ind)) = ?industry && LCASE(STR(?prod)) = ?product)
        { ?e cn:hasLead ?who . BIND("lead" AS ?relation) }
        UNION
        { ?e cn:hasReviewer ?who . BIND("reviewer" AS ?relation) }
        ?who rdfs:label ?name ; cn:role ?title . }
ORDER BY ?relation ?name"""

TRAINING = """\
PREFIX cn:   <https://data.cloudnova.example/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?name ?training
WHERE { ?who a cn:Person ; rdfs:label ?name ; cn:hipaaTraining ?training . }
ORDER BY ?name"""

STATUS = {"trained": "done", "due": "due"}
GRAPH = load_cloudnova()


def query(sparql: str, **args: str):
    """Run one query; the arguments are matched lower-case, so "Healthcare" finds "healthcare"."""
    from rdflib import Literal, Variable

    return list(GRAPH.query(sparql, initBindings={Variable(k): Literal(v.strip().lower()) for k, v in args.items()}))


if __name__ == "__main__":
    server.run()  # stdio: an MCP client starts this file and talks to it over stdin/stdout
