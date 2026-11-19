"""Episode 6: real data. Map tables to a graph, define a metric once, gate what an LLM extracts, match names."""
import csv
import difflib
import logging
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import morph_kgc  # noqa: E402
from rdflib import OWL, RDF, RDFS, SH, XSD, Graph, Literal, Namespace  # noqa: E402

from common.io import LAB_ROOT, number, out_dir, sections, verdict  # noqa: E402
from common.ns import CN, FAM  # noqa: E402
from common.sources import fetch_json  # noqa: E402

logging.disable(logging.CRITICAL)  # keep the output to what the episode shows

HERE = Path(__file__).resolve().parent
SQL = LAB_ROOT / "data" / "cloudnova" / "cloudnova.sql"
SHAPES = LAB_ROOT / "data" / "shapes" / "engagement-shape.ttl"
SOW_PDF = LAB_ROOT / "data" / "docs" / "sow-17.pdf"
NAMES = LAB_ROOT / "data" / "cloudnova" / "acme-names.csv"
MATCH_AT = 0.80  # a name similarity at or above this links automatically; below it, a person reviews the pair
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")
ENTITY_URL = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

PROMPT = """\
Read the statement of work below and write Turtle triples for the engagement it describes.
Use exactly these prefixes and terms:
@prefix cn: <https://data.cloudnova.example/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
Engagement IRI: cn:claims-ai   (a cn:Engagement)
Properties: cn:hasLead, cn:hasReviewer (people: cn:emma, cn:daniel), cn:uses (cn:cirrus-ai), cn:forCustomer (cn:acme-health), cn:startDate.
Write cn:startDate as an ISO date (YYYY-MM-DD).
Return only Turtle, no explanation.

--- SOW ---
"""


def short(term) -> str:
    s = str(term)
    return "cn:" + s[len(CN):] if s.startswith(str(CN)) else term.n3()


def map_tables() -> Graph:
    """CloudNova tables (SQLite) -> RDF, following mapping.rml.ttl."""
    db_file = out_dir() / "cloudnova.db"
    db_file.unlink(missing_ok=True)
    db = sqlite3.connect(db_file)
    db.executescript(SQL.read_text(encoding="utf-8"))
    db.commit()
    db.close()
    config = f"[DataSource1]\nmappings: {HERE / 'mapping.rml.ttl'}\ndb_url: sqlite:///{db_file}\nlogging_level: WARNING\n"
    g = morph_kgc.materialize(config)
    g.bind("cn", CN)
    return g


def cloudnova_db() -> sqlite3.Connection:
    """The CloudNova tables in an in-memory SQLite database."""
    db = sqlite3.connect(":memory:")
    db.executescript(SQL.read_text(encoding="utf-8"))
    return db


def reports() -> list[tuple[str, str, list[str]]]:
    """Each report's own query from reports.sql, run on the tables: (report, what it counts, customers)."""
    db = cloudnova_db()
    text = (HERE / "reports.sql").read_text(encoding="utf-8")
    blocks = re.findall(r"^-- ([^:\n]+): ([^\n]+)\n(SELECT[^;]*);", text, flags=re.M)
    out = [(name, rule, sorted(r[0] for r in db.execute(query))) for name, rule, query in blocks]
    db.close()
    return out


def metric(g: Graph) -> tuple[str, str, list[str]]:
    """Run the metric defined in metrics.ttl: its label, its definition in words, and the customers it counts."""
    m = Graph().parse(HERE / "metrics.ttl", format="turtle")
    label, definition, query = next(iter(m.query(
        "PREFIX cn: <https://data.cloudnova.example/> "
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
        "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> "
        "SELECT ?l ?d ?q WHERE { ?m a cn:Metric ; rdfs:label ?l ; skos:definition ?d ; cn:sparql ?q }"
    )))
    return str(label), str(definition), [str(row[0]) for row in g.query(str(query))]


def verdict_metric(report_counts: list[int], n: int):
    """The reports' numbers against the one definition's number."""
    if len(set(report_counts)) == 1:
        return True, f"The reports already agree on {n}; now it is written down once."
    counts = ", ".join(str(c) for c in report_counts[:-1]) + f" and {report_counts[-1]}"
    return True, f"{number(len(report_counts)).capitalize()} reports said {counts}; one definition says {n}."


def normal(name: str) -> str:
    """Lower case, punctuation to spaces: "ACME-HLTH" -> "acme hlth"."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", name.lower()).split())


def similarity(a: str, b: str) -> float:
    """How alike two names are, 0 to 1: the share of their letters that line up in order (difflib)."""
    return round(difflib.SequenceMatcher(None, normal(a), normal(b)).ratio(), 2)


def match_names(customers: list[str]):
    """Score each source name against each customer, after blocking (same first word only).

    Returns (names, pairs before blocking, [(score, name, source, customer, matched)], best first)."""
    with NAMES.open(encoding="utf-8", newline="") as f:
        names = list(csv.DictReader(f))
    rows = []
    for n in names:
        for c in customers:
            if normal(n["name"]).split()[0] == normal(c).split()[0]:
                score = similarity(n["name"], c)
                rows.append((score, n["name"], n["source"], c, score >= MATCH_AT))
    rows.sort(key=lambda r: (-r[0], r[1]))
    return names, len(names) * len(customers), rows


def verdict_match(rows: list):
    """How many names linked by themselves, and how many wait for a person."""
    matched = [r for r in rows if r[4]]
    review = len(rows) - len(matched)
    targets = sorted({r[3] for r in matched})
    who = targets[0] if len(targets) == 1 else f"{number(len(targets))} customers"
    names = lambda n: f"{number(n).capitalize()} name{'s' if n != 1 else ''}"  # noqa: E731
    goes = f"{number(review)} go{'es' if review == 1 else ''} to a person to review."
    if not review:
        return True, f"{names(len(matched))} matched {who}; nobody needs to review."
    if not matched:
        return None, f"No name scored {MATCH_AT:.2f} or more; {goes}"
    return None, f"{names(len(matched))} matched {who}; {goes}"


def keep_fields(doc: dict) -> dict:
    """Cut a Wikidata entity document down to what the lab uses: English label and the country claim (P17)."""
    out = {}
    for qid, e in doc["entities"].items():
        claims = {"P17": [{"mainsnak": {"property": "P17", "datavalue": {"value": {"id": c["mainsnak"]["datavalue"]["value"]["id"]}}},
                           "rank": c.get("rank", "normal")}
                          for c in e.get("claims", {}).get("P17", []) if "datavalue" in c["mainsnak"]]}
        out[qid] = {"id": e["id"], "labels": {"en": e["labels"]["en"]}, "claims": claims}
    return {"entities": out}


def wikidata(qid: str) -> dict:
    return fetch_json(ENTITY_URL.format(qid), name=f"wikidata-{qid}", trim=keep_fields)["entities"][qid]


def resolve_toronto() -> tuple[Graph, str, str, str]:
    """Resolve fam:toronto against Wikidata (Q172): sameAs, label and country.

    Returns (triples, summary line, label, country label)."""
    city = wikidata("Q172")
    country_id = city["claims"]["P17"][0]["mainsnak"]["datavalue"]["value"]["id"]
    country = wikidata(country_id)
    label, country_label = city["labels"]["en"]["value"], country["labels"]["en"]["value"]
    g = Graph()
    for prefix, ns in (("fam", FAM), ("wd", WD), ("wdt", WDT), ("owl", OWL), ("rdfs", RDFS)):
        g.bind(prefix, ns)
    g.add((FAM.toronto, OWL.sameAs, WD["Q172"]))
    g.add((FAM.toronto, RDFS.label, Literal(label)))
    g.add((FAM.toronto, WDT.P17, WD[country_id]))
    return g, f"fam:toronto → wd:Q172 {label}, {country_label} (from Wikidata)", label, country_label


def extraction() -> str:
    """The LLM's Turtle for the contract page (extract.py, runnable by itself; it imports from this file)."""
    from ep06_real_data.extract import extraction as ask_llm

    return ask_llm()


def parse_turtle(text: str) -> Graph:
    """Models wrap Turtle in code fences; keep only the Turtle."""
    fenced = re.search(r"```(?:turtle|ttl)?\s*\n(.*?)```", text, re.S)
    g = Graph()
    g.parse(data=fenced.group(1) if fenced else text, format="turtle")
    return g


def extracted() -> Graph:
    """The triples the LLM wrote from the contract page (the recorded answer unless LAB_LLM is set)."""
    return parse_turtle(extraction())


def problems(report: Graph) -> dict:
    """A SHACL report as {(node, property, value): (constraint component, message)}."""
    out = {}
    for r in report.subjects(RDF.type, SH.ValidationResult):
        key = (report.value(r, SH.focusNode), report.value(r, SH.resultPath), report.value(r, SH.value))
        out[key] = (report.value(r, SH.sourceConstraintComponent), report.value(r, SH.resultMessage))
    return out


def gate(new: Graph, mapped: Graph):
    """Validate LLM triples in the context of the mapped graph (shape_gate.py, runnable by itself).

    Returns (accepted, quarantined); quarantined is a list of (subject, predicate, object, (component,
    message)) for triples SHACL rejects.
    """
    from ep06_real_data import shape_gate  # it imports from this file, so import it here

    quarantined = shape_gate.gate(new, mapped)
    return kept(new, quarantined), quarantined


def kept(new: Graph, quarantined: list) -> Graph:
    """The new triples the gate did not quarantine."""
    out = Graph()
    for t in new:
        if t not in {q[:3] for q in quarantined}:
            out.add(t)
    return out


def report_gate(new: Graph, quarantined: list):
    """Print the gate section: each rejected triple, the counts, the verdict."""
    accepted = kept(new, quarantined)
    print("== SHACL gate on the LLM's triples ==")
    for s, p, o, (comp, msg) in sorted(quarantined, key=str):
        print(f"REJECTED {short(s)} {short(p)} {lit(o)} -> {component(comp)}: {msg}")
    print(f"accepted: {len(accepted)} of {len(new)} triples")
    print(f"quarantined: {len(quarantined)}")
    verdict(*verdict_gate(new, accepted, quarantined))


def shape_datatype():
    """The datatype the engagement shape asks of cn:startDate (read from the shape, not hard-coded)."""
    shapes = Graph().parse(SHAPES, format="turtle")
    return shapes.value(
        next(shapes.subjects(SH.path, CN.startDate)), SH.datatype
    )


def component(c) -> str:
    dt = shape_datatype()
    return {str(SH.DatatypeConstraintComponent): f"sh:datatype {dt.n3(Graph().namespace_manager)}",
            str(SH.ClassConstraintComponent): "sh:class"}.get(str(c), short(c))


def lit(o) -> str:
    return f'"{o}"' if isinstance(o, Literal) else short(o)


def verdict_api(label: str, country: str):
    return True, f"Linked: our Toronto is Wikidata's {label}, {country} (Q172)."


def verdict_pdf(text: str):
    n = len([line for line in text.splitlines() if line.strip()])
    return None, f"The PDF page is now {number(n)} lines of plain text for the LLM."


def verdict_extract(text: str):
    try:
        n = len(parse_turtle(text))
    except Exception:  # a live model can answer with anything
        return False, "The LLM's answer is not valid Turtle."
    return None, f"The LLM wrote {number(n)} triples. Nothing has checked them yet."


def verdict_gate(extracted: Graph, accepted: Graph, quarantined: list):
    """What the gate did: all accepted, or which value it rejected and how many triples it kept."""
    n, kept = len(extracted), len(accepted)
    if not quarantined:
        return True, f"ACCEPTED: all {number(n)} triples fit the shape."
    if len(quarantined) == 1:
        _, _, o, (comp, _) = quarantined[0]
        if comp == SH.DatatypeConstraintComponent and shape_datatype() == XSD.date:
            return False, f'REJECTED: "{o}" is not a real date. {kept} of {n} triples kept.'
        return False, f"REJECTED: {lit(o)} breaks the shape. {kept} of {n} triples kept."
    return False, f"REJECTED: {len(quarantined)} of {n} triples break the shape; {kept} kept."


def main():
    only = sections(["map", "semantic-layer", "api", "pdf", "extract", "gate", "match"])
    want = lambda name: only is None or name in only  # noqa: E731
    # the mapped graph feeds the map and metric sections and is the context the gate validates in
    mapped = map_tables() if any(want(n) for n in ("map", "semantic-layer", "gate")) else None
    if want("map"):
        print("== map: CloudNova tables to a graph (mapping.rml.ttl) ==")
        print(f"mapped triples: {len(mapped)}")
        for s, p, o in sorted(mapped.triples((None, CN.forCustomer, None))):
            print(f"{short(s)} {short(p)} {short(o)}")
        print()

    if want("semantic-layer"):
        found = reports()
        label, definition, counted = metric(mapped)
        print(f"== semantic layer: {label}, three reports, one definition (metrics.ttl) ==")
        rows = [(f"{name}: {rule}", customers) for name, rule, customers in found]
        mine = (f"{label.lower()}: {definition}", counted)
        width = max(len(r) for r, _ in rows + [mine])
        print("each report counts its own way (reports.sql):")
        for r, customers in rows:
            print(f"  {r:{width}}  {len(customers)}  {', '.join(customers)}")
        print("one definition, for every report (metrics.ttl):")
        print(f"  {mine[0]:{width}}  {len(counted)}  {', '.join(counted)}")
        verdict(*verdict_metric([len(c) for _, _, c in found], len(counted)))
        print()

    # the API answer, the PDF, the LLM's extraction and the gate are their own short files, runnable by
    # themselves (they import from this file): fetch_api.py, read_pdf.py, extract.py and shape_gate.py
    from ep06_real_data import extract, fetch_api, read_pdf, shape_gate

    for slug, module in (("api", fetch_api), ("pdf", read_pdf), ("extract", extract)):
        if want(slug):
            module.main()
            print()
    if want("gate"):
        shape_gate.main(mapped)
        print()

    if want("match"):
        db = cloudnova_db()
        customers = [r[0] for r in db.execute("SELECT name FROM customer ORDER BY name")]
        db.close()
        names, pairs, rows = match_names(customers)
        print(f"== match: Acme's names against our customers ({NAMES.name}) ==")
        print(f"{len(names)} names x {len(customers)} customers = {pairs} pairs; "
              f"blocking keeps {len(rows)} (same first word)")
        w, sw = max(len(r[1]) for r in rows), max(len(r[2]) for r in rows)
        for score, name, source, customer, ok in rows:
            print(f"{score:.2f}  {name:{w}}  {source:{sw}}  " + (f"match: {customer}" if ok else "review queue"))
        print(f"rule: {MATCH_AT:.2f} or more is a match; below that, a person decides")
        verdict(*verdict_match(rows))


if __name__ == "__main__":
    main()
