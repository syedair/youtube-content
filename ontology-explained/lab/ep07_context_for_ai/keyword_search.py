"""Keyword search (BM25): score each chunk by the question's words."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ep07_context_for_ai.step import QUESTION, chunks, show_search, words


def bm25(question, docs, k1=1.5, b=0.75):
    """Rare question words count most; long chunks count a little less."""
    texts = [words(doc) for doc in docs]
    avg = sum(len(t) for t in texts) / len(texts)
    scores = [0.0] * len(texts)
    for word in set(words(question)):
        has = sum(word in t for t in texts)  # how many chunks have it
        idf = math.log((len(texts) - has + 0.5) / (has + 0.5) + 1)
        for i, t in enumerate(texts):
            f = t.count(word)
            length = 1 - b + b * len(t) / avg
            scores[i] += idf * f * (k1 + 1) / (f + k1 * length)
    return scores


def main(rows=None):
    found = chunks()  # (document, paragraph) for every paragraph
    show_search(found, bm25(QUESTION, [text for _doc, text in found]), rows)


if __name__ == "__main__":
    main()
