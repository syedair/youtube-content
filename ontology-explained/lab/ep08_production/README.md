# Episode 8: Ontology in production

## What you'll see

Four things, in order:

1. **Ontology CI.** The checks a pipeline would run on every change: SHACL on the data (`person-shape.ttl` on the Carter facts, `engagement-shape.ttl` on CloudNova) and the four competency questions from `ep09_design/competency-questions.rq`. One line says it all: `ontology CI: SHACL ✓  competency queries 4/4 ✓`. If a check fails the step exits non-zero, which is what makes a CI job go red.
2. **Version diff.** `family-v1.ttl` against `family-v2.ttl`, printed as `+` and `-` lines, for example `+ fam:hasAncestor a owl:TransitiveProperty` and `- fam:birthDate rdfs:range xsd:string`. `family-v2.ttl` is the ontology in `data/ontology/family.ttl`; v1 is an earlier draft.
3. **Provenance.** Each source file is loaded into its own named graph, then a query reports where every fact came from, for example `fam:rose-carter fam:birthName "Rose Lee"  ← source: census-1951.csv`. Rose's birth name appears twice because both sources assert it. In the census it is the `birth_name` column of the row `R. Lee, 20, Toronto`, which the step matches to `fam:rose-carter` by hand (born 1931 in Toronto, so 20 in 1951).
4. **Taxonomy.** `skos-services.ttl` is a SKOS taxonomy of CloudNova services: `cn:cirrus-ai` is a kind of `cn:ai-services`, with a preferred label and alternative labels. A taxonomy says "kind of" and nothing more; it does not say what a service does or who uses it. That is the ontology's job.

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep08_production/ci_checks.py`) and run by themselves; each prints its section of the output:

```
uv run ep08_production/ci_checks.py      # ci
uv run ep08_production/diff_versions.py  # diff
uv run ep08_production/taxonomy.py       # taxonomy
```

To run every part in order:

```
uv run ep08_production/step.py
```

To see just one part, add `--only <section>`: `uv run ep08_production/step.py --only ci`. The sections are `ci`, `diff`, `provenance`, `taxonomy`. An unknown name lists the valid ones and exits with status 2.

## Expected output

```
== ontology CI: the checks a pipeline runs on every change ==
ontology CI: SHACL ✓  competency queries 4/4 ✓
✓ Passed: the data fits every shape, and all four questions get answers.

== version diff: family-v1.ttl -> family-v2.ttl ==
- fam:birthDate rdfs:range xsd:string
+ fam:birthDate rdfs:range xsd:date
+ fam:birthName a owl:DatatypeProperty
+ fam:birthName rdfs:domain fam:Person
+ fam:hasAncestor a owl:TransitiveProperty
+ fam:marriedTo a owl:SymmetricProperty
→ Six changes in meaning: one fact removed, five added.

== provenance: one named graph per source ==
fam:david-carter a fam:Person  ← source: david-tree.csv
fam:david-carter fam:hasChild fam:leo-carter  ← source: david-tree.csv
fam:maya-carter fam:hasChild fam:amy-carter  ← source: maya-photos.csv
fam:rose-carter a fam:Person  ← source: david-tree.csv
fam:rose-carter fam:birthDate "1931-04-03"^^xsd:date  ← source: david-tree.csv
fam:rose-carter fam:birthName "Rose Lee"  ← source: census-1951.csv
fam:rose-carter fam:birthName "Rose Lee"  ← source: david-tree.csv
fam:rose-carter fam:bornIn fam:toronto  ← source: david-tree.csv
fam:rose-carter fam:hasChild fam:david-carter  ← source: david-tree.csv
fam:rose-carter fam:hasChild fam:maya-carter  ← source: maya-photos.csv
fam:rose-carter fam:name "Rose Carter"  ← source: david-tree.csv
fam:rose-carter fam:name "Rose Carter"  ← source: maya-photos.csv

== taxonomy: kind-of and nothing else (skos-services.ttl) ==
cn:cirrus-ai is a kind of cn:ai-services  (prefLabel "Cirrus AI"@en; altLabel "CAI"@en, "Cirrus Intelligence"@en)
→ Three names, one service: Cirrus AI is a kind of AI services.
```

The same text is in `expected.txt`.

## Try this

In `family-v2.ttl`, delete `owl:TransitiveProperty` from `fam:hasAncestor` and run again: the `+ fam:hasAncestor a owl:TransitiveProperty` line disappears from the diff. Then in `data/shapes/person-shape.ttl` change `xsd:date` to `xsd:integer` and watch the CI line turn to `SHACL ✗` and the step exit non-zero.
