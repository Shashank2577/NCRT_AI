import fitz  # PyMuPDF
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PDF_DIR = os.path.join(BASE_DIR, "raw_pdfs")
HEADINGS_OUT = os.path.join(BASE_DIR, "parsed_output", "chapter_candidates.json")
FONT_THRESHOLD = 16.0  # Adjust if needed

def extract_headings():
    all_headings = []
    page_counter = 1

    for root, dirs, files in os.walk(RAW_PDF_DIR):
        pdf_files = sorted([f for f in files if f.endswith(".pdf")])
        for pdf_file in pdf_files:
            pdf_path = os.path.join(root, pdf_file)
            print(f"🔍 Scanning {pdf_file}...")

            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                blocks = page.get_text("dict")["blocks"]
                page_headings = []

                for block in blocks:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            size = span.get("size", 0)
                            if len(text) > 6 and size >= FONT_THRESHOLD:
                                page_headings.append({
                                    "text": text,
                                    "size": round(size, 2)
                                })

                if page_headings:
                    all_headings.append({
                        "global_page_number": page_counter,
                        "source_file": pdf_file,
                        "source_page_number": page_num + 1,
                        "headings": page_headings
                    })

                page_counter += 1

    with open(HEADINGS_OUT, "w", encoding="utf-8") as f:
        json.dump(all_headings, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Headings saved to {HEADINGS_OUT}. Total pages with headings: {len(all_headings)}")

if __name__ == "__main__":
    extract_headings()
