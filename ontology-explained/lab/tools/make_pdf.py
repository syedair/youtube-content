# /// script
# requires-python = ">=3.12"
# dependencies = ["fpdf2==2.8.4"]
# ///
"""Build data/docs/sow-17.pdf from ep06_real_data/sow-17.txt.

usage (from lab/): uv run tools/make_pdf.py
The lab's own environment only needs pypdf to READ the PDF; fpdf2 is used here, once, to write it.
"""
from pathlib import Path

from fpdf import FPDF

LAB = Path(__file__).resolve().parent.parent
SRC = LAB / "ep06_real_data" / "sow-17.txt"
DST = LAB / "data" / "docs" / "sow-17.pdf"

pdf = FPDF(format="A4")
pdf.set_creation_date(__import__("datetime").datetime(2026, 10, 31))  # keep the file reproducible
pdf.set_title("Statement of Work 17")
pdf.add_page()
pdf.set_font("Courier", size=11)
for line in SRC.read_text(encoding="utf-8").splitlines():
    pdf.cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
DST.parent.mkdir(parents=True, exist_ok=True)
pdf.output(str(DST))
print(f"wrote {DST.relative_to(LAB)}")
