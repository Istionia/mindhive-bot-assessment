import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, SecretStr
from typing import List
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
# HuggingFace embeddings imported dynamically to handle fallback properly
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
import pandas as pd
import requests

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env")

# Debug: Print first few characters of API key to verify it's loaded
print(f"API Key loaded: {OPENROUTER_API_KEY[:8]}...")

# Test OpenRouter API directly
try:
    response = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/Istionia/mindhive-bot-assessment",
            "X-Title": "Mindhive Bot Assessment"
        }
    )
    print(f"OpenRouter API test: {response.status_code}")
    if response.status_code == 200:
        print("✓ OpenRouter API key is working")
    else:
        print(f"✗ OpenRouter API error: {response.text}")
except Exception as e:
    print(f"✗ OpenRouter API test failed: {e}")

# Set environment variables for OpenRouter compatibility
os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

# FastAPI app
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Data ingestion and embedding
DATA_FILES = ["data/zus_drinkware.csv", "data/zus_outlets.csv"]

def load_csvs(files: List[str]) -> List[Document]:
    docs = []
    for file in files:
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            # Concatenate all columns for context
            content = " | ".join(str(x) for x in row.values)
            docs.append(Document(page_content=content, metadata={"source": file}))
    return docs

# Global variables for lazy initialization
_rag_chain = None
_retriever = None

def get_rag_chain():
    """Lazy initialization of RAG chain to avoid blocking startup"""
    global _rag_chain, _retriever
    
    if _rag_chain is None:
        print("🔄 Initializing RAG components...")
        
        # Load documents
        documents = load_csvs(DATA_FILES)
        
        # Initialize embeddings with fallback
        try:
            print("🔄 Initializing local HuggingFace embeddings...")
            from langchain_huggingface import HuggingFaceEmbeddings  # type: ignore
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("✅ Local HuggingFace embeddings initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize HuggingFace embeddings: {e}")
            print("🔄 Falling back to OpenRouter embeddings...")
            try:
                if not OPENROUTER_API_KEY:
                    raise RuntimeError("OPENROUTER_API_KEY is required when HuggingFace embeddings fail")
                embeddings = OpenAIEmbeddings(
                    api_key=SecretStr(OPENROUTER_API_KEY),
                    base_url="https://openrouter.ai/api/v1",
                    default_headers={
                        "HTTP-Referer": "https://github.com/Istionia/mindhive-bot-assessment",
                        "X-Title": "Mindhive Bot Assessment"
                    }
                )
                print("✓ OpenAI embeddings initialized with OpenRouter")
            except Exception as e2:
                print(f"✗ Failed to initialize both embeddings: {e2}")
                raise RuntimeError(f"Could not initialize any embeddings: HuggingFace={e}, OpenRouter={e2}") from e2
        
        # Create vector store and chain
        vectorstore = FAISS.from_documents(documents, embeddings)
        _retriever = vectorstore.as_retriever()
        
        llm = ChatOpenAI(
            model="meta-llama/llama-3-70b-instruct", 
            temperature=0,
            api_key=SecretStr(OPENROUTER_API_KEY),
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/Istionia/mindhive-bot-assessment",
                "X-Title": "Mindhive Bot Assessment"
            }
        )
        _rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=_retriever)
        print("✅ RAG chain initialized successfully")
    
    return _rag_chain, _retriever

# Request/response models
class RAGQuery(BaseModel):
    query: str

class RAGResponse(BaseModel):
    answer: str
    sources: List[str]

@app.get("/health")
def health_check():
    """Health check endpoint for deployment"""
    return {"status": "healthy", "message": "ZUS Coffee Bot is running"}

@app.get("/")
def read_root():
    """Serve the chat interface"""
    try:
        return FileResponse('static/index.html')
    except Exception as e:
        # Fallback if static files aren't available
        return {
            "message": "ZUS Coffee Bot API is running!",
            "error": f"Static files not found: {str(e)}",
            "chat_api": "/rag/query",
            "docs": "/docs"
        }

@app.get("/api")
def api_info():
    """API information endpoint"""
    return {
        "message": "Mindhive Bot API is running!",
        "endpoints": {
            "/": "GET - Chat interface",
            "/rag/query": "POST - Ask questions about ZUS products and outlets",
            "/docs": "GET - API documentation"
        },
        "example": {
            "method": "POST",
            "url": "/rag/query",
            "body": {"query": "What drinkware products are available?"}
        }
    }

@app.post("/rag/query", response_model=RAGResponse)
def rag_query(request: RAGQuery):
    try:
        # Initialize components on first request
        rag_chain, retriever = get_rag_chain()
        
        result = rag_chain({"query": request.query}, return_only_outputs=True)
        answer = result["result"]
        # Optionally, return sources (top docs)
        docs = retriever.get_relevant_documents(request.query)
        sources = list({doc.metadata.get("source", "") for doc in docs})
        return RAGResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
