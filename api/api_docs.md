# API Documentation

## Overview
This document describes the API endpoints provided by the Mindhive-Bot backend (`api/`), focusing on Retrieval-Augmented Generation (RAG) and planned Text2SQL capabilities. It also includes a flow diagram of the chatbot setup.

---

## Endpoints

### 1. RAG Query Endpoint

**POST** `/rag/query`

Retrieves relevant information from ingested CSV data and generates an answer using Meta-LLaMA-3.3-70B-Instruct via OpenRouter.

#### Request Body
```json
{
  "query": "string"
}
```

#### Response
```json
{
  "answer": "string",
  "sources": ["string"]
}
```

#### Example
**Request:**
```json
{
  "query": "What drinkware products are available?"
}
```
**Response:**
```json
{
  "answer": "ZUS offers tumblers, mugs, and more. See the full list in the drinkware CSV.",
  "sources": ["data/zus_drinkware.csv"]
}
```

---

### 2. Text2SQL Endpoint (Planned)

**POST** `/text2sql/query` *(planned)*

Converts a natural language question into an SQL query and executes it against the SQLite database (e.g., `db/outlets.db`).

#### Request Body
```json
{
  "query": "string"
}
```

#### Response
```json
{
  "sql": "string",
  "result": [ { "column": "value" } ]
}
```

#### Example
**Request:**
```json
{
  "query": "Which outlets are open after 9pm?"
}
```
**Response:**
```json
{
  "sql": "SELECT * FROM outlets WHERE closing_time > '21:00';",
  "result": [ { "id": 1, "name": "Outlet A", ... } ]
}
```

*Note: This endpoint is a planned feature and not yet implemented.*

---

## Flow Diagram: Chatbot Setup

Below is a high-level flow diagram of the chatbot and RAG pipeline:

```
flowchart TD
    User["User Query"] -->|POST /rag/query| API["FastAPI RAG Endpoint"]
    API --> Retriever["FAISS Vector Store Retriever"]
    Retriever --> Docs["Relevant CSV Rows"]
    Docs --> LLM["Meta-LLaMA-3.3-70B-Instruct (OpenRouter)"]
    LLM --> API
    API -->|Answer + Sources| User
```

---

## Example Chatbot UI Setup

- The backend can be connected to a web or chat UI that sends user queries to `/rag/query` and displays the answer and sources.
- For screenshots or UI code, see your frontend/chatbot integration (not included in this repo).

---

## Notes
- All endpoints expect and return JSON.
- For production, secure the API and consider rate limiting.
