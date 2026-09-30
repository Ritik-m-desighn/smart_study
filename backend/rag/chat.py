import logging
from typing import Dict, Any, List
from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.rag.retriever import get_retriever
from backend.rag.prompts import (
    RAG_SYSTEM_PROMPT,
    OUT_OF_SCOPE_RESPONSE,
    format_rag_context,
    build_rag_user_prompt
)

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.retriever = get_retriever()
        self._client = None

    def _get_client(self):
        if not GEMINI_API_KEY:
            return None
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self._client = None
        return self._client

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Executes the RAG chat pipeline:
        1. Retrieve relevant chunks with similarity thresholding.
        2. If out of scope, return refusal without calling Gemini.
        3. If relevant, pass strictly relevant chunks to Gemini.
        4. Return answer and structured source citations.
        """
        question = question.strip()
        if not question:
            return {
                "answer": "Please ask a question about your study materials.",
                "sources": []
            }

        # 1. Retrieve chunks
        relevant_chunks, is_in_scope = self.retriever.retrieve(question)

        # 2. Retrieval-level protection: refuse immediately if below threshold
        if not is_in_scope or not relevant_chunks:
            return {
                "answer": OUT_OF_SCOPE_RESPONSE,
                "sources": []
            }

        # Format sources list
        sources: List[Dict[str, Any]] = []
        seen_sources = set()
        for chunk in relevant_chunks:
            meta = chunk.get("metadata", {})
            fn = meta.get("filename", "Unknown Document")
            p = meta.get("page")
            s = meta.get("slide")
            source_key = (fn, p, s)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                src_dict: Dict[str, Any] = {"filename": fn}
                if p is not None:
                    src_dict["page"] = int(p)
                if s is not None:
                    src_dict["slide"] = int(s)
                sources.append(src_dict)

        # Format context
        context_str = format_rag_context(relevant_chunks)
        user_prompt = build_rag_user_prompt(question, context_str)

        # 3. Call Gemini if client available
        client = self._get_client()
        if client is not None:
            try:
                from google.genai import types
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=RAG_SYSTEM_PROMPT,
                        temperature=0.2,
                    )
                )
                answer_text = response.text.strip() if response.text else ""
                if not answer_text:
                    answer_text = OUT_OF_SCOPE_RESPONSE
                return {
                    "answer": answer_text,
                    "sources": sources
                }
            except Exception as e:
                logger.error(f"Gemini API generation error: {e}")
                # Fallback to local grounded excerpt if API fails
                return self._fallback_grounded_answer(question, relevant_chunks, sources)

        # Local deterministic grounded fallback (useful during testing or when no API key)
        return self._fallback_grounded_answer(question, relevant_chunks, sources)

    def _fallback_grounded_answer(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deterministic, strictly grounded fallback answer constructed directly from retrieved chunks.
        Used when Gemini API key is not configured or in offline test runs.
        """
        top_chunk = chunks[0]
        meta = top_chunk.get("metadata", {})
        loc = f"[Page {meta['page']}]" if "page" in meta and meta["page"] is not None else (
            f"[Slide {meta['slide']}]" if "slide" in meta and meta["slide"] is not None else ""
        )
        
        # Take the most relevant sentences
        text = top_chunk.get("text", "").strip()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        snippet = lines[0] if lines else text
        
        answer = f"{snippet} {loc}".strip()
        return {
            "answer": answer,
            "sources": sources
        }

# Singleton instance
_chat_service: ChatService | None = None

def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
