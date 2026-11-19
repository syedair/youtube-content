# Episode 9: Design from questions

## What you'll see

The competency questions from the deck's "Start from questions." slide, kept in `competency-questions.rq` as one SPARQL query each. The step runs every question against CloudNova and prints the answer, along with the classes and properties that question needs the ontology to name. Every question has an answer: Daniel Brooks and Emma Clarke for CQ1, Fraud Watch for CQ2, two lab results for CQ3, and Emma Clarke for CQ4.

To make CQ2 and CQ3 answerable, `data/cloudnova/cloudnova.sql` has one engagement without a lead (Fraud Watch) and three lab results for Patient P7: HbA1c with the valid code `4548-4`, one with no code, and one with a made-up local code. CQ3 checks that a LOINC code has the right format (`NNNNN-N`); it does not look codes up in the real LOINC table. Episode 8 runs the same questions in its CI check.

Then one business rule, and who decided it. `data/shapes/hipaa-training-rule.ttl` is a SHACL shape: anyone who leads or reviews a healthcare engagement must finish HIPAA training. Next to the check, the rule carries its own record in standard properties: what it says (`skos:definition`), who owns it (`dcterms:creator`, the CloudNova compliance team), why it exists (`rdfs:comment`) and since when (`dcterms:created`, 2026-10-31). The step prints that record, runs the rule on CloudNova (it flags Emma Clarke, the same person CQ4 names) and checks that the owner, reason and date are written down. A rule is a choice somebody made; written down like this, anyone can see who to ask and challenge it.

## Run it

From the `lab/` folder:

```
uv run ep09_design/step.py
```

To see just one part, add `--only <section>`: `uv run ep09_design/step.py --only cq2`. The sections are `cq1`, `cq2`, `cq3`, `cq4`, one per competency question, and `rule`, the HIPAA training rule with its owner, reason and date. An unknown name lists the valid ones and exits with status 2.

## Expected output

```
Start from questions. Each one is a SPARQL query in competency-questions.rq.

== CQ1: Which employees worked on Cirrus AI engagements for healthcare customers? ==
the ontology must name: cn:Engagement, cn:forCustomer, cn:hasLead, cn:hasReviewer, cn:industry, cn:uses
answer:
  Daniel Brooks
  Emma Clarke

== CQ2: Which engagements have no lead? ==
the ontology must name: cn:Engagement, cn:hasLead
answer:
  Fraud Watch

== CQ3: Which lab results lack a valid LOINC code? ==
the ontology must name: cn:LabResult, cn:forPatient, cn:loincCode
answer:
  Fasting glucose (Patient P7)
  Lipid panel (Patient P7)

== CQ4: Who needs HIPAA training? ==
the ontology must name: cn:Person, cn:hipaaTraining
answer:
  Emma Clarke

== rule: HIPAA training rule, and who decided it (data/shapes/hipaa-training-rule.ttl) ==
rule:  Anyone who leads or reviews a healthcare engagement must finish HIPAA training.
owner: CloudNova compliance team
why:   They can see patient data, and US law (HIPAA) expects training first.
since: 2026-10-31
flags: Emma Clarke
✓ This rule has an owner, a written reason and a date.
```

The same text is in `expected.txt`.

## Try this

1. In `cloudnova.sql`, give Fraud Watch a lead (`'emma'` in the `lead_id` column) and run again: CQ2 now prints `(no answer)`. A question with no answer is a gap in the data or in the ontology.
2. In `data/shapes/hipaa-training-rule.ttl`, delete the `dcterms:creator` line and run `--only rule`: the owner reads `(not written down)` and the last line turns to `✗ No owner: nobody can explain or challenge this rule.` The check still runs; nobody can say who to ask about it.
