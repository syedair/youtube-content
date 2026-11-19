"""The question, then the model's answer alone: no facts, no documents."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from common.llm import ask
from ep07_context_for_ai.step import QUESTION, retrieve, verdict_question
from ep07_context_for_ai.step import verdict_without


def main(rows=None, parts=("question", "without")):
    if "question" in parts:
        print("== the question ==\n" + QUESTION)
        verdict(*verdict_question())
    if "without" in parts:
        if "question" in parts:
            print()
        answer = ask(QUESTION, name="ep07_without").strip()  # just the question
        print("== WITHOUT THE GRAPH ==\n" + answer)
        rows = retrieve() if rows is None else rows  # who it should name
        verdict(*verdict_without(answer, rows))


if __name__ == "__main__":
    main()
