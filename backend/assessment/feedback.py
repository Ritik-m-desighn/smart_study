import logging
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.rag.retriever import get_retriever
from backend.rag.prompts import build_feedback_prompt, format_rag_context
from backend.assessment.quiz_generator import extract_json_from_text

logger = logging.getLogger(__name__)

def generate_feedback(topic: str, incorrect_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates personalized, source-grounded feedback for questions missed during a quiz.
    """
    if not incorrect_questions:
        return {
            "summary": "Outstanding work! You answered all questions correctly.",
            "weak_topics": [],
            "common_misconceptions": [],
            "study_recommendations": []
        }

    # Retrieve context for topic to ground feedback
    retriever = get_retriever()
    relevant_chunks, _ = retriever.retrieve(topic)
    if not relevant_chunks:
        relevant_chunks = retriever.vector_store.similarity_search(topic, top_k=4)
    
    context_str = format_rag_context(relevant_chunks) if relevant_chunks else "No specific course chunks available."

    # Try Gemini if API key is present
    if GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt = build_feedback_prompt(topic, incorrect_questions, context_str)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            if response.text:
                parsed = extract_json_from_text(response.text)
                if parsed and isinstance(parsed, dict) and "summary" in parsed:
                    return parsed
        except Exception as e:
            logger.error(f"Gemini Feedback Generation failed: {e}. Falling back to rule-based feedback.")

    # Rule-based source-grounded feedback fallback
    recommendations = []
    for item in incorrect_questions:
        src = item.get("source", {})
        loc = f"Page {src.get('page')}" if "page" in src else (
            f"Slide {src.get('slide')}" if "slide" in src else "uploaded materials"
        )
        recommendations.append({
            "concept": item.get("question", topic)[:60] + "...",
            "source_citation": f"[{loc}]",
            "advice": f"Review {src.get('filename', 'document')} ({loc}): {item.get('explanation', '')}"
        })

    return {
        "summary": f"You missed {len(incorrect_questions)} question(s) on {topic}. Focus on the grounded explanations below to strengthen your understanding.",
        "weak_topics": [topic],
        "common_misconceptions": [
            f"Review the difference between the correct principle and '{item.get('selected_option')}'"
            for item in incorrect_questions[:2]
        ],
        "study_recommendations": recommendations
    }
