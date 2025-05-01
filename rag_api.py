from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import requests

# === CONFIG ===
CHROMA_DB_DIR = "../vector_store/chroma"
COLLECTION_NAME = "ncert_content"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K = 3
LLM_ENDPOINT = "https://api.deepinfra.com/v1/openai/chat/completions"  # DeepInfra as default
LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
LLM_TOKEN = "xxx"

# === INIT ===
app = FastAPI()
client = PersistentClient(path=CHROMA_DB_DIR)
collection = client.get_collection(COLLECTION_NAME)
model = SentenceTransformer(EMBED_MODEL)

class QuestionRequest(BaseModel):
    question: str
    filters: Optional[dict] = None

class AnswerResponse(BaseModel):
    answer: str
    sources: List[dict]

# === LLM Wrapper ===
def ask_llm(system, question):
    headers = {
        "Authorization": f"Bearer {LLM_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ]
    }
    try:
        res = requests.post(LLM_ENDPOINT, headers=headers, json=payload, timeout=15)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ LLM error: {e}"

# === Core Retrieval Logic ===
def retrieve_context(question: str, filters: Optional[dict] = None):
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
        context = []
        sources = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            context.append(doc)
            sources.append({
                "chunk_id": meta.get("chunk_id", ""),
                "unit": meta.get("unit"),
                "title": meta.get("title"),
                "class": meta.get("class", ""),
                "subject": meta.get("subject", ""),
                "page": meta.get("page"),
                "start_page": meta.get("page"),  # Using page as start_page
                "chunk_index": meta.get("chunk_index", ""),
                "book_version": meta.get("book_version", ""),
                "url": meta.get("reference_url")
            })
        return context, sources
    except Exception as e:
        return [], []

# === API Endpoint ===
@app.post("/ask", response_model=AnswerResponse)
def ask(request: QuestionRequest):
    context_chunks, source_meta = retrieve_context(request.question, request.filters)
    if not context_chunks:
        return AnswerResponse(answer="Sorry, no relevant content found.", sources=[])

    system_prompt = "You are a helpful tutor. Use only the text provided to answer."
    joined_context = "\n\n".join(context_chunks)
    user_query = f"Based on this textbook content, answer: {request.question}"
    full_prompt = f"{joined_context}\n\n{user_query}"
    final_answer = ask_llm(system_prompt, full_prompt)

    return AnswerResponse(answer=final_answer.strip(), sources=source_meta)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
