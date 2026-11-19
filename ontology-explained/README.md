# Why Your AI Agents Get It Wrong: Ontology Explained

Your AI agent is smart. It just doesn't know your business. This video builds an ontology from scratch with one family,
the Carters, and this folder has the hands-on lab: every idea in the video as a small step you can run yourself.

Video: https://youtu.be/yy6PEA5h1vA

## Run the lab

You need **git** and **uv** (no Docker, no Java, no database, no API key). Full setup notes are in [`lab/README.md`](./lab/README.md).

```
git clone https://github.com/syedair/youtube-content.git
cd youtube-content/ontology-explained/lab
uv run check_setup.py          # ends with "✓ lab ready"
uv run ep01_context/step.py    # then ep02 ... ep09
```

Steps that use an LLM or a web API replay saved answers by default, so everything runs offline. `lab/README.md` shows how
to point them at a local Ollama or any OpenAI-compatible server instead.

## Lab steps and where they are in the video

| Step | What it shows | In the video |
|---|---|---|
| `ep01_context` | Scattered facts: one grandma, five names, no matches; one ID fixes it | 2:03 Scattered facts and one ID |
| `ep02_facts` | Two family files merge into one graph; the facts as Turtle | 3:02 Triples, RDF and Turtle |
| `ep03_meaning` | RDFS kinds of things and OWL rules infer facts nobody wrote | 3:56 RDFS · 4:42 OWL rules |
| `ep04_think_check` | A reasoner infers ancestors, SHACL catches the bad date 03/04/31, a rule finds grandparents | 5:45 The reasoner · 6:56 SHACL · 8:18 Your own rules |
| `ep05_ask` | SPARQL questions, a property-graph edge with details, graph algorithms | 8:48 SPARQL · 9:54 Property graphs · 10:48 Graph algorithms |
| `ep06_real_data` | Tables mapped to a graph, Wikidata, one metric defined once (the semantic layer) | 11:33 Real data · 12:52 Wikidata · 13:47 Semantic layer |
| `ep07_context_for_ai` | The same question with no context, with document chunks, and with graph facts; then an agent using the graph through MCP | 15:01 GraphRAG and MCP |
| `ep08_production` | Ontology CI, version diffs, facts traced to their sources | 17:11 Governance and provenance |
| `ep09_design` | Competency questions first, then the rules that answer them | 20:09 Where to start |

## Sources shown in the video

| Source | Link | Short link (QR in the video) |
|---|---|---|
| Ali Ghodsi quote (shared on X) | https://x.com/sarahdingwang/status/2115127551500910634 | `is.gd/3eByzC` |
| Databricks: Announcing GA of Genie Ontology | https://www.databricks.com/blog/announcing-ga-genie-ontology | `is.gd/IvKzeN` |
| AWS: Context intelligence for your data and AI agents (AWS Context) | https://aws.amazon.com/blogs/machine-learning/context-intelligence-for-your-data-and-ai-agents-at-scale/ | `is.gd/Fu7Djx` |
| AWS: Context Ontology Accelerator (What's New) | https://aws.amazon.com/about-aws/whats-new/2026/07/aws-context--ontology-accelarator-generally-available | `is.gd/XNQP3g` |
| aws/context-ontology-accelerator on GitHub | https://github.com/aws/context-ontology-accelerator | `is.gd/NIFvEi` |
| NVIDIA/auto-ontology on GitHub | https://github.com/NVIDIA/auto-ontology | `is.gd/vq7F87` |
| Wikidata: Toronto (Q172) | https://www.wikidata.org/wiki/Q172 | `is.gd/t7q1GT` |
