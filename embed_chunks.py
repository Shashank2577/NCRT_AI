import os
import json
from tqdm import tqdm
from chromadb import PersistentClient
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# === CONFIG ===
CHUNK_DIR = "../parsed_output/chunks"
CHROMA_DB_DIR = "../vector_store/chroma"
COLLECTION_NAME = "ncert_content"
EMBED_MODEL = "all-MiniLM-L6-v2"
PDF_BASE_URL = "file:///C:/Users/shash/OneDrive/Documents/Code/NCRT-app/ncert_ai_parser/raw_pdfs/class_12/chemistry/ncert_chemistry_part2_2024"  # Fixed path to include the subfolder

# === INIT CHROMA ===
os.makedirs(CHROMA_DB_DIR, exist_ok=True)
client = PersistentClient(path=CHROMA_DB_DIR, settings=Settings(allow_reset=True))

if COLLECTION_NAME in [c.name for c in client.list_collections()]:
    collection = client.get_collection(COLLECTION_NAME)
else:
    collection = client.create_collection(COLLECTION_NAME)

# === Load Embedding Model ===
model = SentenceTransformer(EMBED_MODEL)

def slugify(text):
    return ''.join(e if e.isalnum() else '_' for e in text.lower()).strip('_')

# === Process Chunks ===
files = [f for f in os.listdir(CHUNK_DIR) if f.endswith(".json")]

for file in tqdm(files, desc="Embedding chunks"):
    with open(os.path.join(CHUNK_DIR, file), "r", encoding="utf-8") as f:
        data = json.load(f)

    chunk_id = data["chunk_id"]
    text = data["text"].strip()
    source_file = data.get("source_file", "")
    page = str(data.get("start_page", "1"))
    reference_url = f"{PDF_BASE_URL}/{source_file}#page={page}"

    metadata = {
        "chunk_id": chunk_id,
        "unit": str(data.get("unit_number")),
        "title": data.get("chapter_title"),
        "class": data.get("class"),
        "subject": data.get("subject"),
        "source": source_file,
        "page": page,
        "chunk_index": data.get("chunk_index"),
        "book_version": data.get("book_version"),
        "reference_url": reference_url
    }

    if not text:
        continue

    embedding = model.encode(text).tolist()

    try:
        collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata]
        )
    except Exception as e:
        print(f"❌ Error adding {chunk_id}: {e}")

print(f"\n✅ Done embedding {len(files)} chunks into Chroma DB → {CHROMA_DB_DIR}")
