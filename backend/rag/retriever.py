from typing import List, Dict, Any, Tuple
import logging
from backend.config import SIMILARITY_THRESHOLD, TOP_K_CHUNKS
from backend.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)

class Retriever:
    """
    RAG retriever that performs similarity search on ChromaDB,
    filters chunks based on relevance threshold, and provides out-of-scope detection.
    """
    def __init__(self, threshold: float = SIMILARITY_THRESHOLD, top_k: int = TOP_K_CHUNKS):
        self.threshold = threshold
        self.top_k = top_k
        self.vector_store = get_vector_store()

    def retrieve(self, query: str) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Retrieves top relevant chunks for a given query.
        Returns:
          (relevant_chunks, is_in_scope)
          If no chunks meet the threshold, returns ([], False).
        """
        raw_results = self.vector_store.similarity_search(query=query, top_k=self.top_k)
        if not raw_results:
            return [], False

        # Sort by similarity descending
        sorted_results = sorted(raw_results, key=lambda x: x.get("similarity", 0.0), reverse=True)
        top_similarity = sorted_results[0].get("similarity", 0.0)

        # Check if top result passes the minimum relevance threshold
        if top_similarity < self.threshold:
            logger.info(
                f"Query '{query}' top similarity {top_similarity:.3f} below threshold {self.threshold:.3f}. Out of scope."
            )
            return [], False

        # Filter chunks that satisfy the threshold
        relevant = [c for c in sorted_results if c.get("similarity", 0.0) >= self.threshold]

        # If somehow list is empty after filtering
        if not relevant:
            return [], False

        return relevant, True

# Singleton instance
_retriever: Retriever | None = None

def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever
