# Claude prompt: get NVIDIA Auto Ontology running locally

Paste this into Claude Code (or any coding agent) from inside your `auto-ontology` clone.
It was written on 2026-11-08. NVIDIA may have fixed some of this since, so the prompt asks
the agent to check before it changes anything.

---

I'm running NVIDIA Auto Ontology locally with Docker Compose, using NVIDIA's hosted models
(build.nvidia.com) and the Wide World Importers sample database from auto-ontology-eval.
Three things broke for me. For each one, first check whether it still happens in this
version of the repo. Only change code if it does. Show me each change before you make it,
and don't print my API keys or passwords.

1. **Embedding failures during ingestion.** With `EMBED_MODEL=nvidia/nemotron-3.5-embed-1b`,
   batched embedding requests failed with HTTP 500 ("service inference failed"). Single
   inputs worked. Test a batched request against the hosted endpoint. If it fails, switch
   `EMBED_MODEL` in `.env` to `nvidia/nemotron-3-embed-1b`. It's also 2048 dimensions, so
   the vector column doesn't change. Re-ingest after switching.

2. **Structured output rejected by the model API.** The build (semantic compilation)
   failed with HTTP 400 "unknown field guided_json". The app asked for JSON output through
   the NVIDIA-only `nvext.guided_json` field, which the hosted API no longer accepts. In
   `auto_ontology/utils/llm_invoke.py`, add an opt-in `LLM_CLIENT=openai` setting that
   sends every model through LangChain's `ChatOpenAI`, so JSON output uses the standard
   OpenAI `response_format`. Also:
   - Only send `extra_body={"nvext": {"max_thinking_tokens": ...}}` when the base URL is
     an NVIDIA endpoint. Reasoning models otherwise spent the whole token budget thinking
     and returned nothing (`LengthFinishReasonError`).
   - Don't send `temperature` to Claude or GPT-5-family models, which reject it.
   This change is also what lets you point the chat roles at other OpenAI-compatible
   providers (OpenRouter, Ollama, OpenAI, Anthropic, Gemini).

3. **Missing foreign keys (a real bug).** The Postgres connector only picked up foreign
   keys between tables in the same schema. Wide World Importers has 98 foreign keys, and
   59 of them cross schemas (for example `sales.customers.deliverycityid` →
   `application.cities`), so the map missed them and the agent joined tables the wrong
   way. In `auto_ontology/connectors/postgres.py`, `get_fks()` joins
   `information_schema.constraint_column_usage` on `tc.table_schema = ccu.table_schema`.
   `ccu.table_schema` is the *referenced* table's schema, so that should be
   `tc.constraint_schema = ccu.constraint_schema`. Verify by counting foreign keys before
   and after, against `pg_constraint`. Then rebuild the images, re-ingest, and reset the
   semantic layer (`POST /semantic/reset` on the ingestion service). A plain compile
   skips tables that already have terms.

When you're done, tell me what you changed, what you checked, and anything you skipped
because it was already fixed.
