"""The LLM reads the contract and writes triples (saved answer; LAB_LLM)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from common.llm import ask
from common.sources import pdf_text
from ep06_real_data.step import PROMPT, SOW_PDF, verdict_extract


def extraction():
    prompt = PROMPT + pdf_text(SOW_PDF)  # the instructions, then the contract
    return ask(prompt, name="ep06_extract")  # Turtle, as the model wrote it


def main():
    text = extraction()
    print("== the LLM reads sow-17.pdf and writes triples ==")
    print(text.strip())
    verdict(*verdict_extract(text))


if __name__ == "__main__":
    main()
