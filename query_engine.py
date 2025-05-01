import os
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer

# === CONFIG ===
CHROMA_DB_DIR = "../vector_store/chroma"
COLLECTION_NAME = "ncert_content"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3

# === Load Embedding Model ===
model = SentenceTransformer(EMBED_MODEL)

# === Connect to Chroma ===
client = PersistentClient(path=CHROMA_DB_DIR)
collection = client.get_collection(COLLECTION_NAME)

# === Function: Ask Question ===
def ask_question(question, filters=None):
    query_embedding = model.encode(question).tolist()

    query_args = {
        "query_embeddings": [query_embedding],
        "n_results": TOP_K,
        "include": ["documents", "metadatas"]
    }
    if filters:
        query_args["where"] = filters

    try:
        results = collection.query(**query_args)
        answers = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            answers.append({
                "text": doc,
                "unit": meta.get("unit"),
                "title": meta.get("title"),
                "class": meta.get("class"),
                "subject": meta.get("subject"),
                "source_file": meta.get("source"),
                "page": meta.get("page"),
                "reference_url": meta.get("reference_url")
            })
        return answers
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return []

# === CLI Mode ===
if __name__ == "__main__":
    print("Ask a question (Ctrl+C to exit):")
    while True:
        try:
            q = input("\n🧠 > ").strip()
            if not q:
                print("⚠️  Please enter a question.")
                continue

            results = ask_question(q)
            if not results:
                print("❌ No relevant content found.")
                continue

            for i, a in enumerate(results):
                print(f"\n🔹 Result {i+1} (Unit {a['unit']} - {a['title']})")
                print(f"📖 Page: {a['page']} | 🔗 {a['reference_url']}")
                print(a['text'][:800] + ('...' if len(a['text']) > 800 else ''))
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break
