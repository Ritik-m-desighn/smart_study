import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from backend.config import CHROMA_PERSIST_DIRECTORY
from backend.rag.embeddings import get_embedding_service, BaseEmbeddingService

logger = logging.getLogger(__name__)

COLLECTION_NAME = "study_portal_chunks"

class VectorStore:
    """
    Manages vector storage and similarity retrieval using ChromaDB.
    """
    def __init__(
        self,
        persist_dir: Optional[str] = None,
        embedding_service: Optional[BaseEmbeddingService] = None
    ):
        self.persist_dir = persist_dir or str(CHROMA_PERSIST_DIRECTORY)
        self.embedding_service = embedding_service or get_embedding_service()
        
        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.get_or_create_collection()

    def get_or_create_collection(self, name: str = COLLECTION_NAME):
        """
        Creates or retrieves the ChromaDB collection using cosine similarity.
        """
        return self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Computes embeddings and adds chunks to the vector store.
        Each chunk must have:
          - chunk_id
          - document_id
          - text
          - metadata (dict)
        """
        if not chunks:
            return 0

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        
        # Flatten and sanitize metadata for ChromaDB (no nested dicts, all str/int/float/bool)
        metadatas = []
        for c in chunks:
            meta = c.get("metadata", {}).copy()
            meta["document_id"] = c.get("document_id", "")
            meta["chunk_id"] = c.get("chunk_id", "")
            # Ensure values are primitives for ChromaDB
            clean_meta = {}
            for k, v in meta.items():
                if v is None:
                    continue
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                else:
                    clean_meta[k] = str(v)
            metadatas.append(clean_meta)

        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(texts)

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        return len(chunks)

    def delete_document_chunks(self, document_id: str) -> None:
        """
        Deletes all chunks associated with a specific document ID.
        """
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception as e:
            logger.warning(f"Error deleting chunks for document {document_id}: {e}")

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches for top_k most similar chunks to the query string.
        Returns chunk dicts with similarity score, text, and metadata.
        """
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedding_service.embed_query(query)
        
        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": min(top_k, self.collection.count()),
            "include": ["documents", "metadatas", "distances"]
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = self.collection.query(**kwargs)

        retrieved: List[Dict[str, Any]] = []
        if results and results.get("ids") and results["ids"][0]:
            count = len(results["ids"][0])
            for i in range(count):
                chunk_id = results["ids"][0][i]
                text = results["documents"][0][i]
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                distance = results["distances"][0][i] if results.get("distances") else 1.0
                
                # In Chroma cosine distance: similarity = 1 - distance
                similarity = max(0.0, min(1.0, 1.0 - distance))

                retrieved.append({
                    "chunk_id": chunk_id,
                    "text": text,
                    "metadata": metadata,
                    "distance": distance,
                    "similarity": similarity
                })

        return retrieved

# Singleton instance
_vector_store: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
