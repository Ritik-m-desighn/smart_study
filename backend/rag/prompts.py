"""
Prompts for RAG Chat, Quiz Generation, and Feedback.
"""
from typing import List, Dict, Any

RAG_SYSTEM_PROMPT = """You are an AI study assistant.

Your ONLY source of truth is the course material supplied in the CONTEXT.

Rules:

1. Answer only using the supplied context.
2. Never use outside knowledge.
3. Never invent facts.
4. Never invent citations or page numbers.
5. Every factual explanation must be supported by the supplied context.
6. Cite relevant sources using [Page X] or [Slide X].
7. If multiple source locations support the answer, cite all relevant locations.
8. If the context does not contain enough information, say:
   'I couldn't find enough information in the uploaded course material to answer this question.'
9. If the question is clearly outside the uploaded course material, say:
   'This question is outside the scope of the uploaded course material.'
10. Do not fabricate a source.
11. Keep the explanation understandable for a student.
12. Prefer concise answers.
13. Never mention information that is not supported by the provided context."""

OUT_OF_SCOPE_RESPONSE = "This question is outside the scope of the uploaded course material."
INSUFFICIENT_INFO_RESPONSE = "I couldn't find enough information in the uploaded course material to answer this question."

def format_rag_context(chunks: List[Dict[str, Any]]) -> str:
    """
    Formats retrieved chunks into a clearly delimited CONTEXT section.
    """
    formatted_chunks = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata", {})
        filename = meta.get("filename", "Unknown Document")
        
        # Source location tag
        if "page" in meta and meta["page"] is not None:
            loc = f"Page {meta['page']}"
        elif "slide" in meta and meta["slide"] is not None:
            loc = f"Slide {meta['slide']}"
        else:
            loc = f"Section {meta.get('section_index', 1)}"

        chunk_text = c.get("text", "").strip()
        formatted_chunks.append(
            f"--- [CHUNK {i}] Source: {filename} ({loc}) ---\n{chunk_text}"
        )

    return "\n\n".join(formatted_chunks)

def build_rag_user_prompt(question: str, context: str) -> str:
    return f"""=== CONTEXT ===
{context}
=== END CONTEXT ===

Student Question: {question}

Answer the student's question strictly based on the CONTEXT above following all citation and grounding rules."""

def build_quiz_prompt(
    topic: str,
    difficulty: str,
    number_of_questions: int,
    context: str,
    excluded_questions: List[str]
) -> str:
    excluded_text = ""
    if excluded_questions:
        excluded_list = "\n".join(f"- {q}" for q in excluded_questions[:15])
        excluded_text = f"""
DO NOT duplicate or substantially repeat any of the following previously generated questions:
{excluded_list}
"""

    return f"""You are an educational assessment expert.
Generate exactly {number_of_questions} multiple-choice questions (MCQs) for the topic "{topic}" at "{difficulty}" difficulty level.

CRITICAL INSTRUCTIONS:
1. Every question MUST be grounded strictly in the provided course context below.
2. Never invent facts or citations.
3. Every question must have exactly 4 options.
4. Exactly one option must be the correct answer (index 0, 1, 2, or 3).
5. Provide a clear, source-grounded explanation for why the correct answer is right.
6. The source object MUST include the exact page number (e.g. {{"page": 12}}) or slide number (e.g. {{"slide": 5}}) matching the provided chunk metadata.
{excluded_text}
=== COURSE CONTEXT ===
{context}
=== END CONTEXT ===

Respond with ONLY valid JSON adhering to the following JSON schema:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "question": "Question text here?",
      "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
      ],
      "correct_answer": 0,
      "explanation": "Explanation grounded in context",
      "source": {{
        "filename": "document.pdf",
        "page": 1
      }}
    }}
  ]
}}"""

def build_feedback_prompt(
    topic: str,
    incorrect_questions: List[Dict[str, Any]],
    context: str
) -> str:
    items = []
    for i, q in enumerate(incorrect_questions, 1):
        items.append(
            f"Question {i}: {q.get('question')}\n"
            f"Student Selected: {q.get('selected_option')} (Incorrect)\n"
            f"Correct Answer: {q.get('correct_option')} (Correct)\n"
            f"Stored Explanation: {q.get('explanation')}"
        )
    incorrect_str = "\n\n".join(items)

    return f"""You are an AI study tutor providing personalized, encouraging, and source-grounded feedback for a student who just took a quiz on "{topic}".

Rules:
1. Base all feedback strictly on the provided COURSE CONTEXT. Do not make unsupported claims.
2. Identify the weak areas/subtopics indicated by the missed questions.
3. Diagnose the likely misconception behind each mistake.
4. Provide constructive guidance on which concepts or pages/slides to review.

=== COURSE CONTEXT ===
{context}
=== END CONTEXT ===

=== MISSED QUESTIONS ===
{incorrect_str}
=== END MISSED QUESTIONS ===

Respond with ONLY a valid JSON object with the following structure:
{{
  "summary": "High-level diagnostic summary of performance and key learning points",
  "weak_topics": ["subtopic 1", "subtopic 2"],
  "common_misconceptions": ["Misconception 1 explanation", "Misconception 2 explanation"],
  "study_recommendations": [
    {{
      "concept": "concept name",
      "source_citation": "[Page X] or [Slide Y]",
      "advice": "specific advice on what to review"
    }}
  ]
}}"""
