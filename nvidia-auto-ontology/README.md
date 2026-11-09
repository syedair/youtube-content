# NVIDIA Auto Ontology: Give Your AI a Map of Your Database

AI agents guess what your tables and columns mean. NVIDIA's free, open-source Auto Ontology builds a map from your database instead, so the agent knows what things mean and how they join.

This guide has everything from the video: the links, the install commands, the three fixes I needed to get it running, and how to use other AI models with it.

## Links

| | |
|---|---|
| Auto Ontology (Apache 2.0) | https://github.com/NVIDIA/auto-ontology |
| Sample data (Wide World Importers loader) | https://github.com/NVIDIA/auto-ontology-eval |
| Free NVIDIA API key | https://build.nvidia.com |
| My bug report for fix three | https://github.com/NVIDIA/auto-ontology/issues/463 |

## What's in this folder

| File | What it is |
|---|---|
| [`fixes.patch`](./fixes.patch) | Fixes two and three as one patch (`llm_invoke.py`, `postgres.py`) |
| [`claude-fix-prompt.md`](./claude-fix-prompt.md) | The prompt I gave Claude. It checks for and applies all three fixes for you |
| [`other-models.env`](./other-models.env) | `.env` blocks for Ollama, OpenRouter, OpenAI, Claude and Gemini |

## Install

You need Docker, git and [uv](https://docs.astral.sh/uv/).

```bash
uv self update
git clone https://github.com/NVIDIA/auto-ontology.git && cd auto-ontology
cp .env.example .env
```

In `.env`, set `DEFAULT_MODELS_API_KEY` (your build.nvidia.com key), `AUTH_SECRET` (`openssl rand -hex 32`), `APP_URL`, `POSTGRES_PASSWORD`, `AUTO_ONTOLOGY_ADMIN_PASSWORD` and `PGADMIN_PASSWORD`. Leave `CONNECTION_STRINGS` empty and add the database in Settings, Connections instead.

- `AUTO_ONTOLOGY_ADMIN_PASSWORD` is what you type to log in.
- `AUTH_SECRET` signs your session cookie after you log in. You never type it.

Then load the sample data and start everything:

```bash
docker compose up -d --wait postgres
git clone https://github.com/NVIDIA/auto-ontology-eval.git ../auto-ontology-eval
(cd ../auto-ontology-eval && uv sync && cp .env.example .env && \
  POSTGRES_PASSWORD='<same password>' \
  uv run python scripts/seed/seed_wwi.py --database-name wideworldimporters --drop)
docker compose up -d --build
open http://localhost:3000
```

Connect the database in Settings, Connections: host `postgres`, port `5432`, user `postgres`, your `POSTGRES_PASSWORD`. A table deny regex of `_archive$` skips the 17 archive tables. Saving starts building the map.

## The three fixes (tested 2026-11-08)

NVIDIA may have fixed some of these since. Check before you change anything, or paste [`claude-fix-prompt.md`](./claude-fix-prompt.md) into Claude Code from inside your clone and let it check for you.

**Fix one: the default embedding model kept failing.** Batched requests to `nvidia/nemotron-3.5-embed-1b` failed with HTTP 500. Switch to the older model, same size (2048 dimensions):

```bash
EMBED_MODEL=nvidia/nemotron-3-embed-1b
```

**Fix two: the tool asks the AI for a fixed format with an NVIDIA-only setting** (`nvext.guided_json`), and NVIDIA's own cloud API no longer accepts it (HTTP 400 "unknown field guided_json"). The patch adds `LLM_CLIENT=openai`, which uses the common OpenAI-style `response_format` instead. It also caps how long reasoning models think, and skips `temperature` for Claude and GPT-5, which reject it. This is also what lets other models work with the tool.

```bash
LLM_CLIENT=openai
```

**Fix three: a real bug.** The Postgres connector missed every foreign key that crosses a schema, like `sales.customers` to `application.cities`. In this database, that's 59 of 98 links. One line in `get_fks()` fixes it ([issue #463](https://github.com/NVIDIA/auto-ontology/issues/463)).

Apply fixes two and three from the root of your clone:

```bash
curl -sL https://raw.githubusercontent.com/syedair/youtube-content/main/nvidia-auto-ontology/fixes.patch | git apply
docker compose up -d --build
```

After fix three, rebuild the map: re-ingest, then reset the semantic layer (`POST /semantic/reset` on the ingestion service). A plain compile skips tables that already have terms.

## Use other AI models

With fix two in place, the two chat roles (reasoning and non-reasoning) work with any OpenAI-compatible API: Ollama, OpenRouter, OpenAI, Claude or Gemini. Copy one block from [`other-models.env`](./other-models.env) into your `.env`, run `docker compose up -d`, then rebuild the ontology in Settings, Semantic Compilation.

Embeddings and reranking stay on NVIDIA: the vector column is fixed at 2048 dimensions and every embedding request sends NVIDIA-only fields.

## The model comparison

I tested 11 AI models, three times each, with and without an example query.

- Without the example, almost every model got it wrong.
- With it, almost every model got it right.
- Only one got it right every time on its own: Claude Sonnet.
- The model that builds the map matters too. On a map built by Haiku, it was right two in three.
- Sonnet answered in about 30 seconds. NVIDIA's free default took four and a half minutes.

## Connect

- YouTube: https://www.youtube.com/@CodeUCraftAI
- LinkedIn: https://www.linkedin.com/in/syedmuhammadhumair/
- X: https://x.com/smhumair
