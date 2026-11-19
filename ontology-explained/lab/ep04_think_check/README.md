# Episode 4: Think and check

## What you'll see

Four sections, in order. **reason**: an OWL reasoner works out facts nobody wrote, such as `fam:leo-carter fam:hasAncestor fam:rose-carter` (children become parents through `inverseOf`, parents become ancestors, ancestors chain) and `fam:tom-carter fam:marriedTo fam:rose-carter` (marriage is symmetric). **check**: a SHACL shape says a birth date must be an `xsd:date`; Dad's spreadsheet row has `03/04/31`, which fails. **fix**: the same row with the date written as a real date (`dad-spreadsheet-fixed.csv`) loads as `"1931-04-03"^^xsd:date` and passes. **rule**: a SPARQL `CONSTRUCT` rule builds `grandparentOf` facts. SPARQL is the graph's query language; episode 5 explains it, and reads this same rule again.

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep04_think_check/shacl_check.py`) and run by themselves; each prints its section of the output:

```
uv run ep04_think_check/shacl_check.py                                        # check
uv run ep04_think_check/shacl_check.py data/carter/dad-spreadsheet-fixed.csv  # fix
```

To run every part in order:

```
uv run ep04_think_check/step.py
```

To see just one part, add `--only <section>`: `uv run ep04_think_check/step.py --only reason`. The sections are `reason`, `check`, `fix`, `rule`. `check` validates Dad's row as it is (`data/carter/dad-spreadsheet.csv`); `fix` validates the same row with the date written as a real date (`data/carter/dad-spreadsheet-fixed.csv`). An unknown name lists the valid ones and exits with status 2.

## Expected output

```
== reason: what the computer works out ==
fam:amy-carter fam:hasAncestor fam:maya-carter (inferred)
fam:amy-carter fam:hasAncestor fam:rose-carter (inferred)
fam:amy-carter fam:hasParent fam:maya-carter (inferred)
fam:david-carter fam:hasAncestor fam:rose-carter (inferred)
fam:david-carter fam:hasParent fam:rose-carter (inferred)
fam:leo-carter fam:hasAncestor fam:david-carter (inferred)
fam:leo-carter fam:hasAncestor fam:rose-carter (inferred)
fam:leo-carter fam:hasParent fam:david-carter (inferred)
fam:maya-carter fam:hasAncestor fam:rose-carter (inferred)
fam:maya-carter fam:hasParent fam:rose-carter (inferred)
fam:tom-carter fam:marriedTo fam:rose-carter (inferred)

== check: Dad's spreadsheet row against the person shape ==
conforms: False
violation: fam:rose-carter fam:birthDate "03/04/31" -> birthDate must be an xsd:date such as 1931-04-03
✗ REJECTED: "03/04/31" is not a real date. The rule wants 1931-04-03.

== check: after the fix "1931-04-03"^^xsd:date ==
conforms: True
✓ ACCEPTED: the birth date is now a real date, 1931-04-03.

== rule: grandparent ==
PREFIX fam: <https://family.example/id/>
CONSTRUCT { ?gp fam:grandparentOf ?gc }
WHERE     { ?gp fam:hasChild ?p .
            ?p  fam:hasChild ?gc . }

== rule result ==
fam:rose-carter fam:grandparentOf fam:amy-carter
fam:rose-carter fam:grandparentOf fam:leo-carter
```

The same text is in `expected.txt`.

## Try this

Open `data/shapes/person-shape.ttl` and change `xsd:date` to `xsd:integer`. Run again: even the fixed date now fails.
