# Mindhive-Bot

## Overview
Mindhive-Bot is a modular, extensible AI assistant platform that combines data ingestion, retrieval-augmented generation (RAG), and agent-based reasoning. It is designed to answer questions using both structured data (CSV, SQLite) and LLM-powered reasoning, with a simple API interface.

---

## Setup & Run Instructions

1. **Clone the repository**
   ```sh
   git clone <your-repo-url>
   cd mindhive-bot
   ```

2. **Create and activate a virtual environment (recommended):**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   pip install pandas  # (if not already in requirements.txt)
   ```

4. **Set up your `.env` file:**
   - Create a `.env` file in the project root with:
     ```env
     OPENROUTER_API_KEY=your_openrouter_api_key_here
     ```

5. **Prepare data (optional):**
   - To refresh or ingest data, use scripts in the `scripts/` or `ingest/` folders (e.g., `python scripts/scrape_drinkware.py`).

6. **Run the API server:**
   ```sh
   uvicorn api.main:app --reload
   ```

7. **Query the RAG endpoint:**
   - Send a POST request to `http://localhost:$PORT/rag/query` (default: `http://localhost:8000/rag/query`) with JSON body:
     ```json
     { "query": "What drinkware products are available?" }
     ```
   - The response includes an LLM-generated answer and sources used.

---

## Architecture Overview

### Components
- **Data Layer:**
  - `data/` contains CSVs (e.g., drinkware, outlets) and scraped HTML dumps.
  - `db/` contains SQLite databases for structured storage.
  - `scripts/` and `ingest/` provide scraping and ingestion utilities.

- **RAG API:**
  - `api/main.py` exposes a FastAPI app with a `/rag/query` endpoint.
  - Ingests all CSVs, embeds rows using OpenAI-compatible embeddings (via OpenRouter), and stores them in a FAISS vector store.
  - Uses Meta-LLaMA-3.3-70B-Instruct (OpenRouter) for LLM-powered answer generation.

- **Agent Layer:**
  - `agent/` (planned/placeholder) for advanced planning, memory, and tool use.
  - Designed for future extensibility (e.g., multi-step reasoning, tool use, memory).

- **Testing:**
  - `tests/` contains unit and integration tests for core logic and error handling.

### Data Flow
1. **Ingestion:** Data is scraped or loaded from CSV/HTML, optionally stored in SQLite.
2. **Embedding:** CSV rows are embedded and indexed in FAISS for fast retrieval.
3. **Retrieval:** On query, relevant rows are retrieved from the vector store.
4. **Generation:** Retrieved context is sent to the LLM for answer synthesis.
5. **API:** The answer and sources are returned via the FastAPI endpoint.

---

## Key Trade-offs
- **Simplicity vs. Extensibility:**
  - The current RAG pipeline is simple (single endpoint, all CSVs combined), but the architecture allows for future expansion (e.g., more endpoints, agent tools).
- **Performance:**
  - FAISS is in-memory for speed; for large datasets, persistence or sharding may be needed.
- **LLM Cost/Latency:**
  - Each query invokes the LLM via OpenRouter, which may incur cost and latency.
- **Data Freshness:**
  - Data is static unless ingestion scripts are re-run; no real-time sync.
- **Security:**
  - No authentication on the API by default; add security for production use.

---

## Notes
- Ensure your OpenRouter API key has access to Meta-LLaMA-3.3-70B-Instruct.
- For production, consider securing the API and persisting the FAISS index.
- The `agent/` directory is a placeholder for future advanced features.
