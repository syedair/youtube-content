# Recorded model answers

Each `<name>.txt` here is a saved answer from a model, keyed by the `name` passed to `common.llm.ask`; each `<name>.json` is a saved tool-using conversation, one model turn per entry, for `common.llm.chat`.

- `LAB_LLM=recorded` (default): read the saved file. No network, same output every time.
- `LAB_LLM=ollama` or `openai`: ask a live model.
- `LAB_RECORD=1` with a live mode: save the live answer to `<name>.txt`.
- `LAB_LLM_DIR`: read and write somewhere other than this folder.

## What is recorded

Recorded on 2026-10-31 (the three `ep07_*` files again on 2026-11-01, after the episode 7 question and the two job titles changed; `ep07_search.txt` on 2026-11-01 too, when the step gained its search section) with `LAB_LLM=ollama LAB_RECORD=1`, model `llama3.1:8b` (ollama 0.40.13, digest 46e0c10c039e), temperature 0. The files are the model's raw output, unedited.

| File | Used by | What it holds |
|------|---------|---------------|
| `ep06_extract.txt` | ep06_real_data | Turtle the model wrote from the text of `data/docs/sow-17.pdf` (read with pypdf; re-recorded on 2026-10-31 after the step moved from the `.txt` to the PDF, whose extracted text differs in blank lines. The model's answer came out byte-identical). It reads "period 13, day 1" as month 13 and writes `cn:startDate "2026-13-01"^^xsd:date`, which SHACL rejects. The SOW uses the fiscal-calendar wording "period 13, day 1" because, in our tries, plainer dates were converted correctly by this model. |
| `ep07_without.txt` | ep07_context_for_ai | The question alone. The model says it can’t answer, and offers general information about HIPAA training. |
| `ep07_search.txt` | ep07_context_for_ai (`search`) | The question plus the top three chunks a BM25 keyword search found in `data/cloudnova/docs/` (two paragraphs of the HIPAA training reminder and the Acme Health account note's list of engagements). The model says the documents do not answer who built the Cirrus AI solutions, and that Emma needs to finish her HIPAA training. |
| `ep07_with.txt` | ep07_context_for_ai | The question plus facts retrieved by SPARQL. The model names Emma Clarke, the lead, as the one who built it and says she still needs HIPAA training; it leaves out Daniel Brooks, who reviewed. |
| `ep07_agent.json` | ep07_context_for_ai (`agent`) | Same model and settings, through Ollama's OpenAI-compatible tool calling. One entry per model turn, as `common.llm.chat` returned it: the text (`content`) and the tool calls (`id`, `name`, the `arguments` JSON the model wrote). Turn 1 asks for `people_on_projects` (Cirrus AI, healthcare) and `hipaa_training` together; turn 2 is the answer (Emma led, Daniel reviewed, Emma needs training). The tool results are not saved: the step runs them live through the MCP server (`ep07_context_for_ai/graph_mcp.py`). |

A live model, or a different version, may word these differently. To re-record, run the step with `LAB_LLM=ollama LAB_RECORD=1`.
