# Episode 2: Facts

## What you'll see

Dad's file (`david-tree.csv`) has Rose, David and Leo. Aunt Maya's file (`maya-photos.csv`) has Rose, Maya and Amy. Both call her `fam:rose-carter`, so merging them is just adding the facts together: one family graph, one Rose. The step prints the deck's nine-fact excerpt (Rose and David) as Turtle, N-Triples and JSON-LD, and saves the whole merged graph to `out/carter.ttl`.

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep02_facts/merge.py`) and run by themselves; each prints its section of the output:

```
uv run ep02_facts/merge.py    # merge
uv run ep02_facts/formats.py  # turtle, n-triples, json-ld
```

To run every part in order:

```
uv run ep02_facts/step.py
```

To see just one part, add `--only <section>`: `uv run ep02_facts/step.py --only merge`. The sections are `merge`, `turtle`, `n-triples`, `json-ld`. An unknown name lists the valid ones and exits with status 2.

## Expected output

The full text is in `expected.txt`. The key lines:

```
fam:rose-carter children: fam:david-carter, fam:maya-carter
distinct Rose nodes after merge: 1
merged graph: 10 triples
✓ One Rose, not two: both files' facts now sit on one node.
triple count (all formats): 9
✓ Same 9 facts, three spellings: each reads back as the same graph.
```

## Try this

In `lab/data/carter/maya-photos.csv`, change `rose-carter` to `rose-c` on both Rose rows. Run again. Now there are two Roses and the merge no longer snaps together. Shared IRIs are the whole trick.
