# Episode 5: Asking the graph

## What you'll see

A SPARQL query (`ep05_ask/grandchildren.rq`) finds Rose's grandchildren (`Amy, Leo`). Then Rose and Tom's marriage is read two ways from `data/carter/marriage.csv`: the RDF loader keeps a bare triple (subject, predicate, object), while a property graph (networkx) keeps the row's other columns, `since`, `place` and `source`, on the edge itself. For contrast the step prints how RDF 1.2 writes the same details as notes on the triple (printed text: the lab's rdflib does not read RDF 1.2 yet). Then CloudNova's people, engagements, customers and products become a network: betweenness centrality finds the most connected person (`Daniel Brooks`) and a shortest path runs from Emma Clarke to Globex Bank. This step does not call a model.

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep05_ask/ask_sparql.py`) and run by themselves; each prints its section of the output:

```
uv run ep05_ask/ask_sparql.py        # sparql
uv run ep05_ask/property_graph.py    # property-graph
uv run ep05_ask/graph_algorithms.py  # algorithms
```

To run every part in order:

```
uv run ep05_ask/step.py
```

To see just one part, add `--only <section>`: `uv run ep05_ask/step.py --only sparql`. The sections are `sparql`, `property-graph`, `algorithms`. An unknown name lists the valid ones and exits with status 2.

The expected output is in `expected.txt`.

## Expected output

```
== sparql: Rose's grandchildren (ep05_ask/grandchildren.rq) ==
Rose's grandchildren: Amy, Leo
→ Rose has two grandchildren: Amy and Leo.

== property graph: Rose and Tom's marriage (data/carter/marriage.csv) ==
RDF triple:      fam:rose-carter fam:marriedTo fam:tom-carter .
property graph:  (rose-carter)-[:MARRIED_TO {since: 1952, place: "Toronto", source: "marriage certificate"}]->(tom-carter)
RDF 1.2 notes:   fam:rose-carter fam:marriedTo fam:tom-carter {| fam:since 1952 ; fam:place "Toronto" ; fam:source "marriage certificate" |} .
→ One link, three details: on the edge, or as RDF 1.2 notes.

== graph algorithms on CloudNova ==
nodes: 12, edges: 12
most central: Daniel Brooks
shortest path Emma Clarke → Globex Bank: Emma Clarke → Claims AI → Daniel Brooks → Lakehouse → Globex Bank
→ Daniel Brooks sits on the most paths; Emma is four hops from Globex Bank.
```

The same text is in `expected.txt`.

## Try this

1. In `ep05_ask/step.py`, change the `shortest_path` target from `"Globex Bank"` to `"Acme Health"` and run again: the path gets shorter.
2. Edit `ep05_ask/grandchildren.rq` to ask for Rose's children (one `hasChild` hop): the answer becomes `David, Maya`.
3. In `data/carter/marriage.csv`, clear the `source` on Rose and Tom's row (keep the comma) and run `uv run ep05_ask/property_graph.py`: the edge carries two details, and the RDF triple is unchanged.
