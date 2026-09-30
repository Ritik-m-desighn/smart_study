import hashlib
import math
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from backend.config import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class BaseEmbeddingService(ABC):
    """
    Abstract interface for embedding generation to ensure modularity.
    """
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        pass


class GeminiEmbeddingService(BaseEmbeddingService):
    """
    Google Gemini Embedding Service using the current official google-genai SDK.
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model = model or GEMINI_EMBEDDING_MODEL
        self._client = None

    def _get_client(self):
        if not self.api_key:
            return None
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini GenAI client: {e}")
                self._client = None
        return self._client

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        client = self._get_client()
        if client is not None:
            try:
                # google-genai client.models.embed_content
                # Batch processing if texts list is large (limit batches to 30)
                all_embeddings: List[List[float]] = []
                batch_size = 20
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = client.models.embed_content(
                        model=self.model,
                        contents=batch
                    )
                    if hasattr(response, "embeddings") and response.embeddings:
                        for emb in response.embeddings:
                            all_embeddings.append(list(emb.values))
                    elif hasattr(response, "embedding") and response.embedding:
                        all_embeddings.append(list(response.embedding.values))
                if len(all_embeddings) == len(texts):
                    return all_embeddings
            except Exception as e:
                logger.warning(f"Gemini embedding API call failed: {e}. Falling back to deterministic local embedding.")

        # Fallback to deterministic pseudo-embedding (for tests or missing API key)
        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        results = self.embed_texts([text])
        return results[0] if results else [0.0] * 768

    @staticmethod
    def _fallback_embed(text: str, dim: int = 768) -> List[float]:
        """
        Deterministic lightweight pseudo-embedding vector normalized to unit length.
        Allows full offline testing and execution even when an external API key is pending.
        Uses normalized positive feature hashing with stopword damping.
        """
        import re
        stopwords = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'who',
            'where', 'when', 'which', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'from', 'it', 'this', 'that', 'and', 'or', 'be', 'do', 'does'
        }
        words = re.findall(r"\w+", text.lower())
        vec = [0.0] * dim
        for w in words:
            weight = 0.02 if w in stopwords else (1.5 + min(len(w) * 0.2, 2.5))
            h = int(hashlib.sha256(w.encode("utf-8")).hexdigest(), 16) % dim
            vec[h] += weight

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            return [x / norm for x in vec]
        else:
            vec[0] = 1.0
            return vec

# Default singleton instance
_default_embedding_service: Optional[BaseEmbeddingService] = None

def get_embedding_service() -> BaseEmbeddingService:
    global _default_embedding_service
    if _default_embedding_service is None:
        _default_embedding_service = GeminiEmbeddingService()
    return _default_embedding_service
