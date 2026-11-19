# Episode 6: Real data

## What you'll see

Six jobs, one step:

1. `mapping.rml.ttl` maps CloudNova's SQLite tables to a graph with morph-kgc (53 triples, `cn:claims-ai cn:forCustomer cn:acme-health`).
2. Three reports count "active customers" three ways, each with its own query in `reports.sql`: the sales dashboard counts customers billed in the last 90 days (1), the consulting team sheet counts customers with an open engagement (3), and the finance report counts customers with a signed contract (2). Then `metrics.ttl` defines "Active customers" once, as a SPARQL query over the mapped graph: a signed contract and an open engagement. Every report that asks gets the same answer, `2  Acme Health, Globex Bank` (Initech has an open engagement, Fraud Watch, but nothing signed yet). The invoices and contracts are in `data/cloudnova/cloudnova.sql`; "the last 90 days" are counted back from 2026-10-31.
3. A live API: `fam:toronto` is resolved against Wikidata's public entity API (no key), and the step prints `fam:toronto → wd:Q172 Toronto, Canada (from Wikidata)` (plus `owl:sameAs`, the label and the country `wd:Q16`). Only a few fields are taken from the large JSON.
4. A PDF: `data/docs/sow-17.pdf` is read with `pypdf` (`source: sow-17.pdf`), and that text goes to the model.
5. A model reads the PDF's text and writes Turtle. The recorded answer contains `cn:startDate "2026-13-01"^^xsd:date`: the model read "period 13, day 1" of a fiscal calendar as month 13. `data/shapes/engagement-shape.ttl` says a start date must be an `xsd:date`, so SHACL rejects that one triple (`quarantined: 1`) and accepts the other five. (The SOW says "period 13, day 1" because plainer wordings were converted correctly by the model in our tries; the fiscal-calendar wording is what trips it.)
6. Entity resolution: Acme's five names (`data/cloudnova/acme-names.csv`: the CRM, billing, the consulting team's sheet, a SOW PDF and a news story) are matched to our customers. Blocking compares only names that share their first word (5 of the 15 possible pairs). Each pair gets a name similarity from 0 to 1 (Python's `difflib`, after lower-casing and turning punctuation into spaces). A score of 0.80 or more is a match: `ACME Health` 1.00, `ACME-HLTH` 0.90, `Acme Health Inc.` 0.85. Anything lower goes to a person: plain `Acme` (0.53, too short to be sure) and `Acme Hospital Group` (0.53, maybe a different company).

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep06_real_data/shape_gate.py`) and run by themselves; each prints its section of the output:

```
uv run ep06_real_data/fetch_api.py   # api
uv run ep06_real_data/read_pdf.py    # pdf
uv run ep06_real_data/extract.py     # extract
uv run ep06_real_data/shape_gate.py  # gate
```

To run every part in order:

```
uv run ep06_real_data/step.py
```

To see just one part, add `--only <section>`: `uv run ep06_real_data/step.py --only map`. The sections are `map`, `semantic-layer`, `api`, `pdf`, `extract`, `gate`, `match`. An unknown name lists the valid ones and exits with status 2.

The expected output is in `expected.txt`. The model answer is a saved one (`data/llm/ep06_extract.txt`); see `data/llm/README.md` to run it live. The Wikidata answer is a saved snapshot too (`data/api/`, see its README). `sow-17.pdf` is generated from `sow-17.txt` by `uv run tools/make_pdf.py`.

## Expected output

```
== map: CloudNova tables to a graph (mapping.rml.ttl) ==
mapped triples: 53
cn:claims-ai cn:forCustomer cn:acme-health
cn:fraud-watch cn:forCustomer cn:initech
cn:lakehouse cn:forCustomer cn:globex-bank
cn:patient-360 cn:forCustomer cn:acme-health

== semantic layer: Active customers, three reports, one definition (metrics.ttl) ==
each report counts its own way (reports.sql):
  sales dashboard: billed in the last 90 days                 1  Acme Health
  consulting team sheet: has an open engagement               3  Acme Health, Globex Bank, Initech
  finance report: has a signed contract                       2  Acme Health, Globex Bank
one definition, for every report (metrics.ttl):
  active customers: a signed contract and an open engagement  2  Acme Health, Globex Bank
✓ Three reports said 1, 3 and 2; one definition says 2.

== api: Wikidata resolves fam:toronto (Special:EntityData/Q172.json) ==
fam:toronto → wd:Q172 Toronto, Canada (from Wikidata)
fam:toronto owl:sameAs wd:Q172
fam:toronto rdfs:label "Toronto"
fam:toronto wdt:P17 wd:Q16
✓ Linked: our Toronto is Wikidata's Toronto, Canada (Q172).

== pdf: the contract page, read with pypdf ==
source: sow-17.pdf
STATEMENT OF WORK 17
CloudNova Inc. and Acme Health
Page 3 of 5. Scope and staffing
Emma Clarke will lead the Cirrus AI claims assistant (engagement "Claims AI") for
Acme Health, starting 2026, period 13, day 1 (P13 D1) of the Acme Health fiscal
calendar. Daniel Brooks will act as reviewer. Patient data stays in the
customer's account.
→ The PDF page is now seven lines of plain text for the LLM.

...

== SHACL gate on the LLM's triples ==
REJECTED cn:claims-ai cn:startDate "2026-13-01" -> sh:datatype xsd:date: startDate must be an xsd:date such as 2026-03-01
accepted: 5 of 6 triples
quarantined: 1
✗ REJECTED: "2026-13-01" is not a real date. 5 of 6 triples kept.

== match: Acme's names against our customers (acme-names.csv) ==
5 names x 3 customers = 15 pairs; blocking keeps 5 (same first word)
1.00  ACME Health          SOW PDF           match: Acme Health
0.90  ACME-HLTH            billing           match: Acme Health
0.85  Acme Health Inc.     CRM               match: Acme Health
0.53  Acme                 consulting sheet  review queue
0.53  Acme Hospital Group  news              review queue
rule: 0.80 or more is a match; below that, a person decides
→ Three names matched Acme Health; two go to a person to review.
```

Key lines only; the full output is in `expected.txt`.

## Try this

1. Run with `LAB_API=live` to call Wikidata for real instead of reading the saved snapshot: `LAB_API=live uv run ep06_real_data/fetch_api.py` (if you're offline it says so and suggests `LAB_API=recorded`).
2. In `data/shapes/engagement-shape.ttl`, delete the line `sh:datatype xsd:date ;` and run again: the bad date is no longer rejected (`quarantined: 0`).
3. In `ep06_real_data/metrics.ttl`, delete the two lines that ask for a contract (`?contract a cn:Contract ;` and `cn:contractWith ?c .`) and run `--only semantic-layer` again: the one definition now says 3, like the consulting team sheet, and no report's own query had to change. (Its `skos:definition` still says "a signed contract": change the words too, they are part of the definition.)
4. In `ep06_real_data/step.py`, lower `MATCH_AT` from `0.80` to `0.50` and run `--only match`: nothing goes to review any more, so `Acme Hospital Group` is matched to Acme Health without anyone checking it.
