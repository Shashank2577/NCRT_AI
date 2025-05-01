import os, json, re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FULL_TEXT_JSON = os.path.join(BASE_DIR, "parsed_output", "raw_text", "merged_raw_text.json")
CHAPTER_HEADINGS_JSON = os.path.join(BASE_DIR, "parsed_output", "chapter_candidates.json")
CHAPTERS_DIR = os.path.join(BASE_DIR, "parsed_output", "chapters")
os.makedirs(CHAPTERS_DIR, exist_ok=True)

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_chapter_starts(candidates):
    chapters = []
    for entry in candidates:
        for head in entry["headings"]:
            text = head["text"].lower()
            if "unit" in text or "chapter" in text:
                chapters.append({
                    "page": entry["global_page_number"],
                    "title": head["text"]
                })
                break  # one heading per page
    chapters = sorted(chapters, key=lambda x: x["page"])
    return chapters

def split_pages_into_chapters(pages, chapter_starts):
    chapters = []
    for i, chap in enumerate(chapter_starts):
        start = chap["page"]
        end = chapter_starts[i+1]["page"] if i + 1 < len(chapter_starts) else float("inf")
        relevant = [p for p in pages if start <= p["global_page_number"] < end]
        chapters.append({
            "unit_number": i + 1,
            "chapter_title": chap["title"],
            "start_page": start,
            "pages": relevant
        })
    return chapters

def save_chapters(chapters):
    for ch in chapters:
        safe = re.sub(r"[^\w]+", "_", ch["chapter_title"]).lower().strip("_")
        fn = f"unit_{ch['unit_number']}_{safe}.json"
        path = os.path.join(CHAPTERS_DIR, fn)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ch, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {fn}")

if __name__ == "__main__":
    print("📚 Splitting chapters based on font headings + full text...")
    pages = load_json(FULL_TEXT_JSON)
    candidates = load_json(CHAPTER_HEADINGS_JSON)
    chapter_starts = get_chapter_starts(candidates)
    split = split_pages_into_chapters(pages, chapter_starts)
    save_chapters(split)
    print(f"\n✅ {len(split)} chapters saved with full content.")
