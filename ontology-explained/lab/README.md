# Ontology Journey Lab

Hands-on code for the video "Why Your AI Agents Get It Wrong: Ontology Explained". Each part of the video has one small step you can run yourself, built on one story: the Carter family and Grandma Rose.

## Before you start

Episode 1 shows this setup in the terminal (`demos/ep01-setup.sh`).

**You need two things:**

- **git**, to download the lab. Check with `git --version`. (macOS: `xcode-select --install`; Ubuntu/Debian: `sudo apt install git`.)
- **uv**, which fetches the right Python and every library for you. Check with `uv --version`.

It runs on macOS and Linux. On Windows, use WSL (Windows Subsystem for Linux) and run everything inside it.

**Install uv** (once):

```
brew install uv                                     # macOS with Homebrew
curl -LsSf https://astral.sh/uv/install.sh | sh     # macOS or Linux, no Homebrew
```

**Get the lab and check the setup:**

```
git clone https://github.com/syedair/youtube-content.git
cd youtube-content/ontology-explained/lab
uv run check_setup.py
```

`check_setup.py` prints your Python version, the installed version of each library the lab uses (rdflib, pySHACL,
OWL-RL, networkx, morph-kgc, pypdf, openai), whether a local Ollama is running (optional: it says
`optional: not running` and carries on; it only ever contacts this machine), and ends with `✓ lab ready`. If a
library is missing it ends with a red `✗ lab not ready` line and exits with status 1. Then run the first step:
`uv run ep01_context/step.py`.

**What the first run downloads:** uv reads `pyproject.toml` and `uv.lock`, downloads a Python (3.12 or newer) if your machine has none, creates `lab/.venv`, and installs the pinned libraries (rdflib, pySHACL, OWL-RL, networkx, morph-kgc, pypdf, the OpenAI client and their dependencies, about 40 packages). That takes a few seconds on a fast connection. Later runs start at once and need no network.

**Not needed:** Docker, Java, a database, an API key or an account anywhere. Steps that use an LLM or a web API replay saved answers by default.

**Optional extras:**

- [Ollama](https://ollama.com) and `ollama pull llama3.1:8b`, only to get live LLM answers in episodes 6 and 7 (`LAB_LLM=ollama`).
- An internet connection, only for `LAB_API=live` (episode 6 asks Wikidata live instead of reading its saved answer).

**Troubleshooting:**

- An LLM error or a hang: go back to the saved answers with `LAB_LLM=recorded` (the default; unset `LAB_LLM`).
- A Wikidata error: go back to the saved copy with `LAB_API=recorded` (the default; unset `LAB_API`).
- A broken download or a strange install error: `uv cache clean`, then run the step again.

## How steps work

Run every step from this `lab/` folder:

```
uv run ep01_context/step.py
```

Each step prints the same output every time. Next to it, `expected.txt` shows what you should see. Files a step creates go to `lab/out/`.

After each result a step prints one line in plain English that says what it means: `✓` when something passes, `✗` when it fails, `→` for an answer. In a terminal they are green, red and bold (set `NO_COLOR=1` to turn colour off, `FORCE_COLOR=1` to keep it when you pipe the output).

## Episodes

| Step | What it does |
|------|--------------|
| ep01_context | Scattered facts: one grandma, five names, no matches |
| ep02_facts | Two family files merge into one graph; a nine-fact excerpt as Turtle, N-Triples and JSON-LD |
| ep03_meaning | An ontology lets the computer infer facts nobody wrote; RDFS lets the Globex Bank typo through, OWL's disjointWith catches it |
| ep04_think_check | A reasoner infers ancestors, SHACL catches the bad date 03/04/31, a rule finds grandparents |
| ep05_ask | SPARQL asks for Rose's grandchildren; Rose and Tom's marriage as a property-graph edge with details vs a bare RDF triple; graph algorithms find the most central person and a shortest path in CloudNova |
| ep06_real_data | Tables map to a graph (morph-kgc), three reports count "active customers" three ways until one metric defines it once, SHACL rejects an LLM's impossible start date, and Acme's names are matched (or sent to a person) |
| ep07_context_for_ai | The same question to an LLM with no context, with chunks a keyword search finds in documents, and with facts retrieved from the graph, then to an agent that calls the graph as tools through an MCP server |
| ep08_production | Ontology CI (SHACL and competency queries), a version diff of two ontology versions, facts traced to their source files, and a SKOS taxonomy |
| ep09_design | Four competency questions, written first, each answered by a SPARQL query on CloudNova; then one business rule with its owner, reason and date |

## LLM and API settings

Steps that talk to a model or a web API use saved answers by default, so they print the same thing every time and need no network. To go live, set:

| Variable | Meaning |
|----------|---------|
| `LAB_LLM` | `recorded` (default), `ollama` or `openai` |
| `LAB_MODEL` | model name (default `llama3.1:8b`) |
| `OLLAMA_BASE_URL` | ollama endpoint (default `http://localhost:11434/v1`) |
| `OPENAI_BASE_URL`, `OPENAI_API_KEY` | endpoint and key for `LAB_LLM=openai` (leave the key unset for a local server that needs none) |
| `LAB_API` | `recorded` (default: the saved Wikidata snapshots in `data/api/`) or `live` (fetch from wikidata.org) |
| `LAB_RECORD=1` | save the live answer into `data/llm/` (with `LAB_LLM` live) or the live API response into `data/api/` (with `LAB_API=live`) |
