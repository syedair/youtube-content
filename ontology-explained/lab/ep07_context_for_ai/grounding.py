"""Grounding: put the graph's facts in the prompt, then ask the model."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from common.llm import ask
from ep07_context_for_ai.step import QUESTION, facts_block, retrieve
from ep07_context_for_ai.step import verdict_with

PROMPT = """\
Answer the question using only the facts below. \
Do not use anything else you know. \
Cite the facts you rely on by quoting the person and engagement. \
If the facts do not answer the question, say so.

Facts:
{facts}

Question: {question}"""


def main(rows):
    prompt = PROMPT.format(facts=facts_block(rows), question=QUESTION)
    answer = ask(prompt, name="ep07_with").strip()
    print("== WITH THE GRAPH ==\n" + answer)
    verdict(*verdict_with(answer, rows))


if __name__ == "__main__":
    main(retrieve())  # the facts from the graph, by SPARQL
