from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import os
import json
import sqlite3
import openai
import faiss
from openai import OpenAI
import numpy as np

# --- existing outlet code omitted for brevity ---

# --- RAG CONFIGURATION ---
EMBEDDING_MODEL = "text-embedding-ada-002"
FAISS_INDEX_PATH = os.getenv('PRODUCTS_INDEX_PATH', 'db/products.index')
PRODUCTS_META_PATH = os.getenv('PRODUCTS_META_PATH', 'db/products.json')
TOP_K = 5

router = APIRouter()

# Load FAISS index and metadata once at startup
try:
    faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    with open(PRODUCTS_META_PATH, 'r', encoding='utf-8') as f:
        products_meta = json.load(f)  # expect list of { "id": ..., "title": ..., "description": ... }
except Exception as e:
    raise RuntimeError(f"Failed to load FAISS index or metadata: {e}")

class ProductQAResponse(BaseModel):
    answer: str
    sources: list[str] = Field(
        ..., description="List of product IDs or titles used as grounding sources."
    )

def embed_text(text: str) -> list[float]:
    client = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY"), base_url=os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"))
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return resp.data[0].embedding

def retrieve_docs(query: str, k: int = TOP_K) -> list[dict]:
    vec = embed_text(query)
    D, I = faiss_index.search(np.array([vec]).astype('float32'), k)
    docs = []
    for idx in I[0]:
        if idx < len(products_meta):
            docs.append(products_meta[idx])
    return docs

def generate_answer(query: str, docs: list[dict]) -> str:
    # Build context from retrieved docs
    context = "\n\n".join(
        f"Product ID: {d['id']}\nTitle: {d['title']}\nDescription: {d['description']}"
        for d in docs
    )
    prompt = (
        f"You are a product assistant. Use ONLY the following product information to answer the user.\n\n"
        f"{context}\n\nUser Question: {query}\nAnswer:"
    )
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"),
    )
    resp = client.chat.completions.create(
        model="meta-llama/llama-3-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = resp.choices[0].message.content
    if content is None:
        raise ValueError("No content returned from LLM")
    return content.strip()

@router.get("/products/qa", response_model=ProductQAResponse)
async def products_qa(query: str = Query(..., description="Natural-language question about products")):
    if not query:
        raise HTTPException(status_code=400, detail="`query` parameter is required.")
    try:
        docs = retrieve_docs(query)
        if not docs:
            raise HTTPException(status_code=404, detail="No relevant products found.")
        answer = generate_answer(query, docs)
        sources = [d.get('title') or str(d.get('id')) for d in docs]
        return ProductQAResponse(answer=answer, sources=sources)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG processing error: {e}")