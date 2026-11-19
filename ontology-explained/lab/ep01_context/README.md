# Episode 1: Scattered facts

## What you'll see

Grandma Rose shows up in five places under five different names: "Nana", "Rose C.", "CARTER, ROSE", "R. Lee" and "Mom". The step loads all five sources and tries the obvious thing, joining them on the name. It finds nothing.

Cloudnova has the same problem with its customer Acme Health: the CRM says "Acme Health Inc.", the consulting team's sheet "Acme", billing "ACME-HLTH", the SOW PDF "ACME Health" and the email thread "the hospital". No two are spelled the same, so a plain join links none of them. Then the step does the fix: a small who-is-who table (`data/cloudnova/who-is-who.csv`) says which real customer each system's name means, so all five names get one ID, `acme-health`. In a real company that table lives in your warehouse or a master data tool; episode 6 shows how the matching is done at scale.

The last section runs the same fix on Grandma's five names, with her own table (`data/carter/who-is-who.csv`): one ID, `rose-carter`.

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep01_context/exact_match.py`) and run by themselves; each prints its section of the output:

```
uv run ep01_context/sources.py      # sources
uv run ep01_context/exact_match.py  # naive-join
uv run ep01_context/lookup.py       # one-id
```

To run every part in order:

```
uv run ep01_context/step.py
```

To see just one part, add `--only <section>`: `uv run ep01_context/step.py --only sources`. The sections are `sources`, `naive-join`, `one-id` (Acme Health), `family-id` (Grandma). An unknown name lists the valid ones and exits with status 2.

## Expected output

```
One grandma. Five names.

== sources ==
1951 census          name            "R. Lee"
Dad's spreadsheet    name            "Rose C."
Family group chat    contact name    "Nana"
Her passport         surname, given  "CARTER, ROSE"
Maya's photo album   caption         "Mom"

== naive join: exact string match on name ==
exact-match pairs: 0
✗ The computer finds no match: five names, zero links.

Same person? You know it. The computer doesn't.

== one ID: look up Acme's five names in who-is-who.csv ==
before the table, exact-match pairs: 0
CRM               "Acme Health Inc."  → acme-health
consulting sheet  "Acme"              → acme-health
billing           "ACME-HLTH"         → acme-health
SOW PDF           "ACME Health"       → acme-health
email             "the hospital"      → acme-health
distinct customers: 1
✓ Five names, one ID: the computer now sees one customer.

== family ID: the same fix for Grandma's five names ==
1951 census          "R. Lee"        → rose-carter
Dad's spreadsheet    "Rose C."       → rose-carter
Family group chat    "Nana"          → rose-carter
Her passport         "CARTER, ROSE"  → rose-carter
Maya's photo album   "Mom"           → rose-carter
distinct people: 1
✓ Five names, one ID: the computer now sees one person.
```

The same text is in `expected.txt`.

## Try this

Open `lab/data/carter/` and change "Mom" in `photo-album.json` to "Nana". Run the step again. You now get one match, but only because you fixed the data by hand. The who-is-who table is the better fix: the sources stay as they are.

Then run the same fix on Grandma: `uv run ep01_context/step.py --only family-id`. Her five names all point to `rose-carter`. Open `data/carter/who-is-who.csv` and change the census row's ID to `rose-c`. Run it again: two IDs for one grandma. The table is only as good as the person who checks it.
