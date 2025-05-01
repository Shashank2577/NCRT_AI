import os
import re
import json
import fitz  # PyMuPDF


def slugify(text):
    return re.sub(r'[^\w]+', '_', text.strip().lower()).strip('_')


def clean_lines(lines):
    clean = []
    prev = ""
    for l in lines:
        l = l.strip()
        if not l or l.isdigit() or l == prev or l.lower().startswith("reprint"):
            continue
        clean.append(l)
        prev = l
    return clean


def extract_title(page):
    lines = page.get_text("text").splitlines()
    candidates = [l for l in lines if not l.strip().isdigit() and len(l.strip()) > 5]
    return candidates[0] if candidates else "Unknown"


def detect_chapter_breaks(doc):
    breaks = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        lower = text.lower()
        if "after studying this unit" in lower or "objectives" in lower:
            breaks.append(i)
    return sorted(set(breaks))


def parse_pdf(pdf_path, out_dir, class_num, subject, book_name, book_version, config=None):
    doc = fitz.open(pdf_path)
    filename = os.path.basename(pdf_path)
    unit = None
    title = None

    # Try extracting from filename pattern: "Unit 6 Haloalkanes and Haloarenes.pdf"
    match = re.match(r"unit[\s_\-]*(\d+)[\s_\-]+(.+)\.pdf", filename, re.IGNORECASE)
    if match:
        unit = int(match.group(1))
        title = match.group(2).replace("_", " ").replace("-", " ").strip()

    # If no filename match, try config
    if (not unit or not title) and config and filename in config:
        unit = config[filename].get("unit")
        title = config[filename].get("chapter_title")

    # If unit and title are found, treat whole PDF as one chapter
    if unit and title:
        all_text = []
        page_nums = []
        for page in doc:
            lines = page.get_text("text").splitlines()
            all_text.extend(clean_lines(lines))
            page_nums.append(page.number + 1)

        chapter = {
            "class": class_num,
            "subject": subject,
            "book_name": book_name,
            "book_version": book_version,
            "unit_number": unit,
            "chapter_title": title,
            "pages": page_nums,
            "start_page": page_nums[0],
            "source_file": filename,
            "text": "\n".join(all_text)
        }

        fn = f"unit_{unit}_{slugify(title)}.json"
        with open(os.path.join(out_dir, fn), "w", encoding="utf-8") as f:
            json.dump(chapter, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved (from filename/config): {fn}")
        return

    # Fallback: detect chapters by content
    chapter_starts = detect_chapter_breaks(doc)
    if not chapter_starts:
        print(f"⚠️ No chapters found in {filename}")
        return

    for idx, start in enumerate(chapter_starts):
        end = chapter_starts[idx + 1] if idx + 1 < len(chapter_starts) else len(doc)
        pages = range(start, end)
        all_text = []
        page_nums = []
        for p in pages:
            page = doc[p]
            lines = page.get_text("text").splitlines()
            all_text.extend(clean_lines(lines))
            page_nums.append(p + 1)

        title = extract_title(doc[start])
        chapter = {
            "class": class_num,
            "subject": subject,
            "book_name": book_name,
            "book_version": book_version,
            "unit_number": idx + 1,
            "chapter_title": title,
            "pages": page_nums,
            "start_page": page_nums[0],
            "source_file": filename,
            "text": "\n".join(all_text)
        }

        fn = f"unit_{idx+1}_{slugify(title)}.json"
        with open(os.path.join(out_dir, fn), "w", encoding="utf-8") as f:
            json.dump(chapter, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved (auto): {fn}")


if __name__ == "__main__":
    BASE = "../raw_pdfs"
    OUT_DIR = "../parsed_output/chapters"
    os.makedirs(OUT_DIR, exist_ok=True)

    for root, _, files in os.walk(BASE):
        pdfs = [f for f in files if f.endswith(".pdf")]
        if not pdfs:
            continue

        path_parts = root.split(os.sep)
        if len(path_parts) < 3:
            continue

        class_folder = path_parts[-3]
        subject = path_parts[-2]
        book_folder = path_parts[-1]

        class_num = class_folder.replace("class_", "")
        version = re.search(r"\d{4}", book_folder)
        book_version = version.group() if version else ""
        book_name = book_folder.replace(f"_{book_version}", "") if book_version else book_folder

        config_path = os.path.join(root, "book_config.json")
        config = None
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

        for pdf in pdfs:
            pdf_path = os.path.join(root, pdf)
            parse_pdf(pdf_path, OUT_DIR, class_num, subject, book_name, book_version, config)
