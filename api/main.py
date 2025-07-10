import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.schema import Document
import pandas as pd

# Load environment variables
load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env")

# Set environment variables for OpenRouter compatibility
os.environ["OPENAI_API_KEY"] = OPENROUTER_API_KEY
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"

# FastAPI app
app = FastAPI()

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

# Prepare vector store with simplified configuration
documents = load_csvs(DATA_FILES)
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

# Prepare retriever and LLM
retriever = vectorstore.as_retriever()
llm = ChatOpenAI(
    model="meta-llama/llama-3-70b-instruct", 
    temperature=0
)
rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# Request/response models
class RAGQuery(BaseModel):
    query: str

class RAGResponse(BaseModel):
    answer: str
    sources: List[str]

@app.post("/rag/query", response_model=RAGResponse)
def rag_query(request: RAGQuery):
    try:
        result = rag_chain({"query": request.query}, return_only_outputs=True)
        answer = result["result"]
        # Optionally, return sources (top docs)
        docs = retriever.get_relevant_documents(request.query)
        sources = list({doc.metadata.get("source", "") for doc in docs})
        return RAGResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
