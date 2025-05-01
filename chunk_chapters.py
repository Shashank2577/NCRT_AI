import os
import json
import re
from tqdm import tqdm
import fitz  # PyMuPDF
from pathlib import Path
from urllib.parse import quote
import nltk
import sys

# === CONFIG ===
CHAPTER_DIR = "../parsed_output/chapters"
CHUNK_DIR = "../parsed_output/chunks"
RAW_PDF_ROOT = "../raw_pdfs"
MAX_TOKENS = 300  # Approx. token count threshold

os.makedirs(CHUNK_DIR, exist_ok=True)

# === NLTK Setup ===
def setup_nltk():
    """Ensure NLTK punkt tokenizer is properly downloaded."""
    try:
        # Try to find the existing punkt data
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('tokenizers/punkt_tab')  # Check for punkt_tab as well
        print("✅ NLTK punkt tokenizer already downloaded.")
    except LookupError:
        print("⏳ NLTK punkt tokenizer or punkt_tab not found. Downloading...")
        try:
            nltk.download('punkt')
            nltk.download('punkt_tab')  # Download punkt_tab explicitly
            print("✅ Successfully downloaded punkt tokenizer and punkt_tab.")
        except Exception as e:
            print(f"❌ Error downloading punkt tokenizer or punkt_tab: {e}")
            print("\nPlease try manually downloading with:\n")
            print("import nltk")
            print("nltk.download('punkt')")
            print("nltk.download('punkt_tab')")
            sys.exit(1)

    # Verify the tokenizer works
    from nltk.tokenize import sent_tokenize
    try:
        test_text = "This is a test. Let's see if it works."
        sentences = sent_tokenize(test_text)
        if len(sentences) != 2:
            raise Exception("Tokenizer didn't split sentences correctly")
        return sent_tokenize
    except Exception as e:
        print(f"❌ Error testing tokenizer: {e}")
        print("Please check your NLTK installation and try again.")
        sys.exit(1)

# Initialize the tokenizer
sent_tokenize = setup_nltk()

# === Approximate tokenizer ===
def num_tokens(text):
    return len(text.split())

# === Chunking utility ===
def chunk_text(text, max_tokens):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    token_count = 0

    for sentence in sentences:
        sentence_tokens = num_tokens(sentence)
        if token_count + sentence_tokens > max_tokens:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                token_count = 0
        current_chunk.append(sentence)
        token_count += sentence_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

# === Map each sentence to page (via fitz) ===
def extract_text_by_page(pdf_path):
    page_map = []
    try:
        with fitz.open(pdf_path) as doc:
            for i, page in enumerate(doc):
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: b[1])
                text = "\n".join(b[4].strip() for b in blocks if b[4].strip())
                page_map.append((i + 1, text))
    except FileNotFoundError:
        print(f"Error: File not found - {pdf_path}")
        return None
    return page_map

# === Main Chunking Process ===
def process_chapters():
    for fname in tqdm(os.listdir(CHAPTER_DIR), desc="🔍 Chunking chapters"):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(CHAPTER_DIR, fname), "r", encoding="utf-8") as f:
            chapter = json.load(f)

        chapter_text = chapter["text"]
        pdf_file = Path(RAW_PDF_ROOT) / f"class_{chapter['class']}" / chapter["subject"] / f"{chapter['book_name']}_2024" / chapter["source_file"]

        # Check if the PDF file exists
        if not pdf_file.exists():
            print(f"Error: PDF file does not exist - {pdf_file}")
            continue

        page_map = extract_text_by_page(pdf_file)
        if page_map is None:
            continue

        sentence_page = {}
        for page_num, page_text in page_map:
            for sentence in sent_tokenize(page_text):
                normalized = re.sub(r"\s+", " ", sentence.strip())[:50]
                sentence_page[normalized] = page_num

        chunks = chunk_text(chapter_text, MAX_TOKENS)
        for i, chunk in enumerate(chunks):
            preview = re.sub(r"\s+", " ", chunk.strip())[:50]
            matched_page = sentence_page.get(preview, chapter.get("start_page", 1))

            # Get the absolute path of the PDF file and convert it to a proper file URL
            # This ensures we have the full path including drive letter
            pdf_abs_path = pdf_file.resolve()
            safe_path = quote(str(pdf_abs_path).replace("\\", "/"))
            reference_url = f"file:///{safe_path}#page={matched_page}"

            chunk_data = {
                "chunk_id": f"{Path(fname).stem}_chunk{i+1}",
                "unit_number": chapter.get("unit_number"),
                "chapter_title": chapter.get("chapter_title"),
                "class": chapter.get("class"),
                "subject": chapter.get("subject"),
                "book_name": chapter.get("book_name"),
                "book_version": chapter.get("book_version"),
                "source_file": chapter.get("source_file"),
                "start_page": matched_page,
                "chunk_index": i + 1,
                "reference_url": reference_url,
                "text": chunk
            }

            with open(os.path.join(CHUNK_DIR, f"{chunk_data['chunk_id']}.json"), "w", encoding="utf-8") as out:
                json.dump(chunk_data, out, indent=2)

if __name__ == "__main__":
    process_chapters()
    print("\n✅ Chunking complete.")
