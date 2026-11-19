# Episode 7: Context for AI

## What you'll see

One question, asked three ways: "Which employees built Cirrus AI solutions for healthcare customers, and who still needs HIPAA training?"

- Without the graph, the model gets the question alone. The recorded answer starts "I can’t answer that." It cannot know these invented people.
- With search, the model gets the three chunks of Cloudnova's documents that look most like the question. `data/cloudnova/docs/` holds five short documents a company would have: a summary of the Claims AI statement of work, the Patient 360 project page, an email thread about the Claims AI design review, a HIPAA training reminder from the compliance team, and a CRM note about Acme Health. The step cuts them into 16 chunks (one per paragraph) and ranks the chunks with BM25, a keyword score written out in a few lines of `keyword_search.py` (the demo shows it with `cat`): a question word counts more when it is rare across the chunks and frequent in this one. Real systems usually rank by vector similarity instead; the idea is the same, text that looks like the question. The top three are the two paragraphs of the training reminder and the account note's list of engagements. The staffing line ("Emma Clarke will lead the engagement. Daniel Brooks will act as reviewer.") scores zero: it shares no word with the question. In the recorded run the model says the documents do not say who built the Cirrus AI solutions, and that Emma needs to finish her HIPAA training.
- With the graph, a SPARQL query retrieves two facts (Emma Clarke, lead, training due; Daniel Brooks, reviewer, training done) and the model answers from only those. In the recorded run it names Emma, who led Claims AI, and says her training is due; it leaves out Daniel, who only reviewed. The step prints the question, the query, the facts, then the three answers: no context, search, graph.
- As an agent, the model gets the graph as tools instead of facts. `graph_mcp.py` is a small MCP (Model Context Protocol) server with two tools, `people_on_projects(product, industry)` and `hipaa_training()`, each a SPARQL query over the same Cloudnova graph. The step starts that server over stdio as a real MCP client, lists its tools, hands them to the model with the same question, runs each tool call the model asks for through MCP, and prints the trace: the tools offered, each call and what the graph said, then the model's answer. In the recorded run the model asks for both tools in its first turn and answers in its second: Emma led the project, Daniel reviewed it, and Emma still needs HIPAA training.

The answers are saved model output, so the step prints the same thing every time. A live model may word them differently; the retrieved chunks and facts never change. For the agent, the model's turns (which tools to call, with which arguments, and the final answer) are saved in `data/llm/ep07_agent.json`; the MCP server and its tool results always run live, because they are local and read the graph.

You can also start the server by itself, for any MCP client (it talks over stdin/stdout): `uv run ep07_context_for_ai/graph_mcp.py`.

## Run it

From the `lab/` folder. The parts the demos show are short files you can read (`cat ep07_context_for_ai/keyword_search.py`) and run by themselves; each prints its section of the output:

```
uv run ep07_context_for_ai/ask_alone.py       # question, without
uv run ep07_context_for_ai/graph_facts.py     # facts
uv run ep07_context_for_ai/keyword_search.py  # search
uv run ep07_context_for_ai/grounding.py       # with
uv run ep07_context_for_ai/agent.py           # agent
```

To run every part in order:

```
uv run ep07_context_for_ai/step.py
```

To see just one part, add `--only <section>`: `uv run ep07_context_for_ai/step.py --only question`. The sections are `question`, `sparql`, `facts`, `without`, `search`, `with`, `agent`. An unknown name lists the valid ones and exits with status 2.

The expected output is in `expected.txt`.

## Expected output

```
== the question ==
Which employees built Cirrus AI solutions for healthcare customers, and who still needs HIPAA training?
→ A question about our own company's data, not the public web.

== sparql: retrieve the facts from the graph ==
PREFIX cn:   <https://data.cloudnova.example/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?name ?relation ?engagement ?customer ?product ?training
WHERE { ?e a cn:Engagement ;
           cn:forCustomer ?c ;
           cn:uses ?p ;
           rdfs:label ?engagement .
        ?c cn:industry "healthcare" ; rdfs:label ?customer .
        ?p rdfs:label "Cirrus AI" , ?product .
        { ?e cn:hasLead ?who . BIND("lead" AS ?relation) }
        UNION
        { ?e cn:hasReviewer ?who . BIND("reviewer" AS ?relation) }
        ?who rdfs:label ?name ;
             cn:hipaaTraining ?training . }
...

== WITHOUT THE GRAPH ==
I can’t answer that. I can help you with general information about HIPAA training.
→ No context: the model cannot answer.

== WITH SEARCH OVER DOCUMENTS ==
Five documents in data/cloudnova/docs, cut into 16 chunks (one per paragraph).
Keyword search (BM25) for the question; the top three:
  1. hipaa-training-reminder.txt  score 5.3  "Hi Emma, from today anyone who leads or ..."
  2. hipaa-training-reminder.txt  score 4.3  "Our records show your HIPAA training is due. ..."
  3. acme-health-account-note.txt  score 4.0  "Open engagements: Claims AI, a claims assistant on ..."
The model's answer, from those chunks only:
Unfortunately, the provided documents do not answer the question about which employees built Cirrus AI solutions for healthcare customers. They only mention that Emma needs to finish HIPAA training before working with patient data on Claims AI.
...
→ Search found three similar chunks; it gets Emma's training, not who built it.
...
→ With the facts, it names Emma.

== agent: the model calls the graph as tools, through MCP ==
MCP server: ep07_context_for_ai/graph_mcp.py, started over stdio
...
model asks (turn 1): people_on_projects(product="Cirrus AI", industry="healthcare")
graph says:          Emma Clarke (Consultant): lead on Claims AI for Acme Health
                     Daniel Brooks (Chief Architect): reviewer on Claims AI for Acme Health
model asks (turn 1): hipaa_training()
graph says:          Daniel Brooks: HIPAA training done
                     Emma Clarke: HIPAA training due
model answers (turn 2):
...
As for who still needs HIPAA training, the response indicates that Emma Clarke needs to complete her HIPAA training.
→ Two tool calls through MCP; the answer names Emma and Daniel.
```

Key lines only; the full output is in `expected.txt`.

## Try this

1. Change `QUESTION` in `ep07_context_for_ai/step.py`; the retrieved facts stay the same, so the answer rests on them.
2. Raise `TOP_K` in `ep07_context_for_ai/step.py` from 3 to 6 and run `--only search`. The Patient 360 project page, the reminder's subject line and the SOW's scope come in, but the SOW's staffing line still does not: it scores zero, because "lead" and "reviewer" are not words in the question. (The recorded answer stays the same, since it was saved for the top three; with Ollama, `LAB_LLM=ollama` lets your model read the new chunks.)
3. Add a document to `data/cloudnova/docs/`, say a team page that reads "Emma Clarke and Daniel Brooks built the Cirrus AI claims assistant for Acme Health, a healthcare customer." Run `--only search` again: it tops the list, because its words are the question's words. Search finds the answer when one paragraph happens to say it all, in the question's words; the graph follows the links, whatever words the documents use.
4. In `data/cloudnova/cloudnova.sql`, set Emma's `hipaa_training` to `'trained'` and run again: the facts block and the recorded answer disagree, which shows why you re-record (`LAB_LLM=ollama LAB_RECORD=1`). In the `agent` section the MCP tool result changes too (it runs live), while the recorded answer still says Emma.
5. With Ollama running, `LAB_LLM=ollama uv run ep07_context_for_ai/agent.py` lets your own model pick the tools. Why does `hipaa_training` take no argument? In our first tries it took one person's name. llama3.1:8b asked for both tools in its first turn, before it had any names, so it made up names for the training lookups and the graph answered "No person named ...". A small model plans badly across steps, so these tools need no step-by-step plan.
