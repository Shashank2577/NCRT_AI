from chromadb import PersistentClient
import json

client = PersistentClient(path="../vector_store/chroma")
collection = client.get_collection("ncert_content")

print("🔍 Total Chunks:", collection.count())

# 1. List how many chunks are from page 1
results = collection.get(include=["metadatas"])
page_counts = {}
for meta in results["metadatas"]:
    page = meta.get("page", "missing")
    page_counts[page] = page_counts.get(page, 0) + 1

print("\n📄 Chunks by Page:")
for page, count in sorted(page_counts.items()):
    print(f"Page {page}: {count} chunks")

# 2. List metadata keys in one random chunk
print("\n🔬 Sample metadata from first chunk:")
print(json.dumps(results["metadatas"][0], indent=2))

# 3. Try a filtered query
query = "What are phenols?"
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode(query).tolist()


response = collection.query(
    query_embeddings=[embedding],
    n_results=5,
    where={"class": "12", "subject": "chemistry"},
    include=["documents", "metadatas"]
)

print(f"\n🔁 Filtered result count: {len(response['documents'][0])}")
for meta in response["metadatas"][0]:
    print(f"✅ Title: {meta.get('title')} | Page: {meta.get('page')}")
