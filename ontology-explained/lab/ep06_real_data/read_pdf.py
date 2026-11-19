"""Read the contract page out of the PDF as plain text, with pypdf."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.io import verdict
from common.sources import pdf_text
from ep06_real_data.step import SOW_PDF, verdict_pdf


def main():
    print("== pdf: the contract page, read with pypdf ==")
    print(f"source: {SOW_PDF.name}")
    page = pdf_text(SOW_PDF).strip()  # the text of every page
    print(page)
    verdict(*verdict_pdf(page))


if __name__ == "__main__":
    main()
