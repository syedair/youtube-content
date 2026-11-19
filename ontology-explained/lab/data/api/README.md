# Recorded API snapshots

`common.sources.fetch_json` reads `<name>.json` from here by default (`LAB_API=recorded`). `LAB_API=live` calls the API; add `LAB_RECORD=1` to save the snapshot.

| File | Fetched from | Fetched on |
|------|--------------|------------|
| `wikidata-Q172.json` | `https://www.wikidata.org/wiki/Special:EntityData/Q172.json` (Toronto) | 2026-10-31 |
| `wikidata-Q16.json` | `https://www.wikidata.org/wiki/Special:EntityData/Q16.json` (Canada) | 2026-10-31 |

Both are the real responses, trimmed by code (`keep_fields` in `ep06_real_data/step.py`) to the only fields episode 6 uses: `labels.en`, and the country claim `P17` (for Toronto it points to `Q16`). The full responses are about 250 KB each; nothing here was written by hand. No API key is needed; requests send the User-Agent `ontology-journey-lab/1.0 (https://github.com/syedair/youtube-content)`.
