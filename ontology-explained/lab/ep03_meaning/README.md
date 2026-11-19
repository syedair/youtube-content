# Episode 3: Meaning

## What you'll see

Three sections, in order. **inferred**: the step builds the ten Carter facts, loads the ontology `data/ontology/family.ttl`, and runs an RDFS reasoner. The ontology says `bornIn` points to a `Place` and `hasChild` points to a `Person`, so the reasoner works out facts nobody wrote, such as `fam:toronto a fam:Place`. Only those new facts are printed.

**trap**: the Cloudnova side. `ep03_meaning/works-on.ttl` holds Globex Bank as the CRM has it (a `cn:Customer`) and two facts someone typed in: Daniel works on Patient 360, and the typo "Globex Bank works on Lakehouse" (they meant Lakehouse is for Globex Bank). The RDFS lines of `data/ontology/cloudnova.ttl` say `worksOn` has domain `Employee` and range `Engagement`, so RDFS makes Globex Bank an Employee, with no error.

**clash**: the same facts with the whole Cloudnova ontology, including its one OWL line, `cn:Person owl:disjointWith cn:Organization`. An OWL reasoner (the OWL RL profile, the one episode 4 uses) works out that Globex Bank is a Person (worksOn's domain, Employee is a kind of Person) and an Organization (it is a Customer, a kind of Organization), and reports the contradiction. The step prints both chains, the reasoner's own message, and a verdict.

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep03_meaning/reasoner.py`) and run by themselves; each prints its section of the output:

```
uv run ep03_meaning/rdfs_infer.py  # trap
uv run ep03_meaning/reasoner.py    # clash
```

To run every part in order:

```
uv run ep03_meaning/step.py
```

To see just one part, add `--only <section>`: `uv run ep03_meaning/step.py --only inferred` prints only the inferred facts, without the count of written facts above them. The sections are `inferred`, `trap`, `clash`. `trap` reads `ep03_meaning/works-on.ttl` with the RDFS lines of `data/ontology/cloudnova.ttl`; `clash` reads the same facts with all of it. An unknown name lists the valid ones and exits with status 2.

## Expected output

```
Written down: 10 facts. Plus the ontology's rules.

== inferred by RDFS (nobody wrote these) ==
fam:amy-carter a fam:Person (inferred from range)
fam:leo-carter a fam:Person (inferred from range)
fam:maya-carter a fam:Person (inferred from range and domain)
fam:toronto a fam:Place (inferred from range)

inferred facts: 4

== trap: RDFS reads the typed facts (ep03_meaning/works-on.ttl) ==
rule: cn:worksOn domain cn:Employee, range cn:Engagement
cn:daniel a cn:Employee (inferred from domain)
cn:globex-bank a cn:Employee (inferred from domain)
cn:lakehouse a cn:Engagement (inferred from range)
cn:patient-360 a cn:Engagement (inferred from range)
errors: 0
✗ No error, no warning: RDFS made Globex Bank an Employee.

== clash: OWL adds cn:Person disjointWith cn:Organization ==
why cn:globex-bank is a Person:
  cn:globex-bank cn:worksOn cn:lakehouse  => a cn:Employee (domain)
  cn:Employee subClassOf cn:Person        => a cn:Person
why cn:globex-bank is an Organization:
  cn:globex-bank a cn:Customer            (written down)
  cn:Customer subClassOf cn:Organization  => a cn:Organization
reasoner: Disjoint classes cn:Person and cn:Organization have a common individual cn:globex-bank
✗ CONTRADICTION: Globex Bank can't be a Person and an Organization.
```

The same text is in `expected.txt`.

## Try this

1. Open `lab/data/ontology/family.ttl` and delete the `rdfs:range fam:Place` line under `fam:bornIn`. Run again. Toronto is no longer known to be a place.
2. Fix the typo in `ep03_meaning/works-on.ttl`: change the last line to `cn:lakehouse cn:forCustomer cn:globex-bank .` and run `--only trap,clash`. Globex Bank stays a Customer, and the reasoner reports `CONSISTENT`.
3. Put the typo back and delete the `owl:disjointWith` line from `data/ontology/cloudnova.ttl`. The clash is gone too: without "never", OWL has nothing to contradict.
