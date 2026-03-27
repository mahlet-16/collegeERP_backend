from pypdf import PdfReader
from pathlib import Path

pdf_path = Path(r"C:\Users\Pavilion\Downloads\CollegeERP (2) (4).pdf")
out_path = Path(r"C:\Users\Pavilion\collegeERP_backend\collegeerp_pdf_extracted.txt")

reader = PdfReader(str(pdf_path))
chunks = []
for i, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""
    chunks.append(f"\n\n===== PAGE {i} =====\n\n{text}")

out_path.write_text("".join(chunks), encoding="utf-8")
print(f"pages={len(reader.pages)}")
print(f"written={out_path}")
