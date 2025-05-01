import os, json, re

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_JSON_PATH = os.path.join(BASE_DIR, "parsed_output", "raw_text", "merged_font_text.json")
CHAPTERS_DIR = os.path.join(BASE_DIR, "parsed_output", "chapters")
os.makedirs(CHAPTERS_DIR, exist_ok=True)

# Font size threshold (can tune this!)
CHAPTER_FONT_THRESHOLD = 16.0

def load_pages():
    with open(RAW_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def is_probable_title(span):
    text = span["text"]
    size = span["size"]
    if size < CHAPTER_FONT_THRESHOLD:
        return False
    if len(text.split()) < 3:
        return False
    if text.strip().isdigit():
        return False
    if any(x in text.lower() for x in ["example", "objectives", "solution", "figure", "exercise"]):
        return False
    return True

def extract_chapter_candidates(pages):
    chapters = []
    for pg in pages:
        for span in pg["spans"]:
            if is_probable_title(span):
                chapters.append({
                    "page_num": pg["global_page_number"],
                    "title": span["text"],
                    "source_file": pg["source_file"]
                })
                break  # Only take first good match on a page
    return chapters

def split_into_chapters(pages, titles):
    result = []
    titles_sorted = sorted(titles, key=lambda x: x["page_num"])
    for idx, title in enumerate(titles_sorted):
        start = title["page_num"]
        end = titles_sorted[idx+1]["page_num"] if idx+1 < len(titles_sorted) else float("inf")
        chapter_pages = [p for p in pages if start <= p["global_page_number"] < end]

        unit_number = idx + 1
        chapter = {
            "unit_number": unit_number,
            "chapter_title": title["title"],
            "source_file": title["source_file"],
            "start_global_page": start,
            "pages": chapter_pages
        }
        result.append(chapter)
    return result

def save_chapters(chapters):
    for ch in chapters:
        safe = re.sub(r"[^\w]+", "_", ch["chapter_title"]).lower().strip("_")
        fn = f"unit_{ch['unit_number']}_{safe}.json"
        with open(os.path.join(CHAPTERS_DIR, fn), "w", encoding="utf-8") as f:
            json.dump(ch, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {fn}")

if __name__ == "__main__":
    pages = load_pages()
    titles = extract_chapter_candidates(pages)
    chapters = split_into_chapters(pages, titles)
    save_chapters(chapters)
    print(f"\n✅ {len(chapters)} chapters saved cleanly.")
