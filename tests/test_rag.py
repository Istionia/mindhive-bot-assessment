from typing import List

from langchain.schema import Document


class RAGRetriever:
    """
    Wraps a FAISS (or any LangChain vectorstore) to return the top-k documents
    for a query, remapping metadata['source'] to metadata['id'] to match tests.
    """
    def __init__(self, vectorstore, k: int = 4):
        self.vectorstore = vectorstore
        self.k = k

    def get_relevant_documents(self, query: str) -> List[Document]:
        # Perform vectorstore similarity search
        docs = self.vectorstore.similarity_search(query, k=self.k)
        results: List[Document] = []
        for doc in docs:
            # Copy metadata and rename 'source' → 'id' if present
            metadata = dict(doc.metadata)
            if "source" in metadata:
                metadata["id"] = metadata.pop("source")
            results.append(Document(page_content=doc.page_content, metadata=metadata))
        return results


class RAGPipeline:
    """
    A minimal RAG pipeline that:
      1) Retrieves relevant docs
      2) Builds a prompt combining context + question
      3) Calls `generate()` to produce an answer

    Tests will stub out `generate()`, so it needs to exist.
    """
    def __init__(self, retriever: RAGRetriever):
        self.retriever = retriever

    async def run(self, query: str) -> str:
        # 1) Retrieve
        docs = self.retriever.get_relevant_documents(query)
        # 2) Build prompt
        prompt = self._build_prompt(query, docs)
        # 3) Generate
        return await self.generate(prompt)

    def _build_prompt(self, query: str, docs: List[Document]) -> str:
        context = "\n".join(doc.page_content for doc in docs)
        return f"Context:\n{context}\n\nQuestion: {query}"

    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Placeholder for actual LLM generation.
        Tests should monkey-patch this method.
        """
        raise NotImplementedError("LLM generation not implemented yet.")

