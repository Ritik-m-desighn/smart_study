import uuid
import json
import re
import logging
from typing import List, Dict, Any, Optional
from backend.config import GEMINI_API_KEY, GEMINI_MODEL
from backend.database import get_db
from backend.rag.retriever import get_retriever
from backend.rag.prompts import build_quiz_prompt, format_rag_context

logger = logging.getLogger(__name__)

def _normalize_quiz_question(question: Any) -> Optional[Dict[str, Any]]:
    """Return a clean, schema-valid question or reject malformed model output."""
    if not isinstance(question, dict):
        return None

    question_text = question.get("question")
    options = question.get("options")
    correct_answer = question.get("correct_answer")
    explanation = question.get("explanation")
    source = question.get("source", {})
    if (
        not isinstance(question_text, str)
        or not question_text.strip()
        or not isinstance(options, list)
        or len(options) != 4
        or type(correct_answer) is not int
        or not 0 <= correct_answer < 4
        or not isinstance(explanation, str)
        or not explanation.strip()
        or not isinstance(source, dict)
    ):
        return None

    clean_options = []
    for option in options:
        if not isinstance(option, str):
            return None
        clean_option = re.sub(r"\s+", " ", option).strip().strip("\"'")
        clean_option = re.sub(r"^\s*(?:[A-Da-d]|\d+)[.)]\s*", "", clean_option)
        clean_option = clean_option.rstrip(" .!?")
        word_count = len(re.findall(r"\b[\w'-]+\b", clean_option))
        if (
            not clean_option
            or word_count > 30
            or re.search(r"\b(?:page|slide)\s*[:#]?\s*\d+\b|\[CHUNK\b", clean_option, re.IGNORECASE)
        ):
            return None
        clean_options.append(clean_option)

    if len({option.casefold() for option in clean_options}) != 4:
        return None

    return {
        "question": question_text.strip(),
        "options": clean_options,
        "correct_answer": correct_answer,
        "explanation": explanation.strip(),
        "source": source
    }

def jaccard_similarity(text1: str, text2: str) -> float:
    """
    Computes token-level Jaccard similarity between two strings to detect duplicates.
    """
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

def is_duplicate_question(new_q: str, existing_questions: List[str], threshold: float = 0.65) -> bool:
    """
    Verifies whether a candidate question is substantially similar to any previous question.
    """
    for ex in existing_questions:
        if jaccard_similarity(new_q, ex) >= threshold:
            return True
    return False

def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Safely extracts and parses JSON even if wrapped in markdown code blocks.
    """
    text = raw_text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try extracting content between ```json and ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Try finding the first '{' and last '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except Exception:
            pass

    return None

class QuizGenerator:
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

    def _get_existing_questions(self, topic: str) -> List[str]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT question_text FROM questions WHERE topic = ? COLLATE NOCASE",
                (topic.strip(),)
            )
            return [row["question_text"] for row in cursor.fetchall()]

    def generate_quiz(
        self,
        topic: str,
        difficulty: str = "medium",
        number_of_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Generates topic-specific MCQs grounded strictly in course materials.
        """
        # 1. Retrieve course context for topic
        relevant_chunks, is_in_scope = self.retriever.retrieve(topic)

        if not is_in_scope or not relevant_chunks:
            raise ValueError(
                f"I couldn't find course material relevant enough to '{topic}'. "
                "Try a topic that appears in your uploaded notes, or upload material about this topic."
            )

        chunk_sizes = [
            len(chunk.get("text", ""))
            for chunk in relevant_chunks
        ]
        logger.info(
            "Quiz retrieval for topic %r: %d chunks, character lengths %s",
            topic,
            len(relevant_chunks),
            chunk_sizes
        )
        context_str = format_rag_context(relevant_chunks)
        existing_questions = self._get_existing_questions(topic)

        # 2. Build prompt
        prompt = build_quiz_prompt(
            topic=topic,
            difficulty=difficulty,
            number_of_questions=number_of_questions,
            context=context_str,
            excluded_questions=existing_questions
        )

        questions_data: List[Dict[str, Any]] = []

        # 3. Call Gemini
        client = self._get_client()
        if client is not None:
            try:
                from google.genai import types
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        response_mime_type="application/json"
                    )
                )
                if response.text:
                    parsed = extract_json_from_text(response.text)
                    if parsed and "questions" in parsed and isinstance(parsed["questions"], list):
                        for raw_question in parsed["questions"]:
                            question = _normalize_quiz_question(raw_question)
                            if question is None:
                                logger.warning("Discarding malformed quiz question from Gemini output.")
                                continue
                            already_seen = existing_questions + [q["question"] for q in questions_data]
                            if not is_duplicate_question(question["question"], already_seen):
                                questions_data.append(question)
                    else:
                        logger.warning("Gemini returned quiz output without a valid questions array.")
            except Exception as e:
                logger.error(f"Gemini quiz generation failed: {e}")

        # Never fill a quiz with repetitive placeholder questions. A short quiz is
        # better than showing students made-up, misleading, or low-quality items.
        if len(questions_data) < number_of_questions:
            if client is None:
                reason = "Gemini is unavailable. Check GEMINI_API_KEY and the model configuration."
            else:
                reason = "Gemini did not return enough distinct, valid questions for these notes."
            raise ValueError(
                f"Couldn't create a reliable {number_of_questions}-question quiz on '{topic}'. "
                f"{reason} Try a narrower topic or add more course material."
            )

        # 5. Persist quiz and questions to SQLite
        quiz_id = str(uuid.uuid4())
        persisted_questions: List[Dict[str, Any]] = []

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO quizzes (id, topic, difficulty, total_questions)
                VALUES (?, ?, ?, ?)
                """,
                (quiz_id, topic, difficulty, len(questions_data))
            )

            for q in questions_data:
                q_id = str(uuid.uuid4())
                q_text = q.get("question", "")
                options = q.get("options", ["A", "B", "C", "D"])
                # Ensure 4 options
                while len(options) < 4:
                    options.append(f"Additional option {len(options)+1}")
                options = options[:4]

                corr_ans = int(q.get("correct_answer", 0))
                if corr_ans < 0 or corr_ans > 3:
                    corr_ans = 0

                explanation = q.get("explanation", "Grounded in uploaded material.")
                source = q.get("source", {})
                if not isinstance(source, dict):
                    source = {}

                # If source is missing page/slide, attach from top chunk
                if "page" not in source and "slide" not in source and relevant_chunks:
                    meta = relevant_chunks[0].get("metadata", {})
                    source["filename"] = meta.get("filename", "Course Document")
                    if "page" in meta:
                        source["page"] = meta["page"]
                    if "slide" in meta:
                        source["slide"] = meta["slide"]

                cursor.execute(
                    """
                    INSERT INTO questions (id, quiz_id, topic, difficulty, question_text, options_json, correct_answer_index, explanation, source_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        q_id,
                        quiz_id,
                        topic,
                        difficulty,
                        q_text,
                        json.dumps(options),
                        corr_ans,
                        explanation,
                        json.dumps(source)
                    )
                )

                persisted_questions.append({
                    "id": q_id,
                    "question": q_text,
                    "options": options,
                    "correct_answer": corr_ans,
                    "explanation": explanation,
                    "source": source,
                    "topic": topic,
                    "difficulty": difficulty
                })

        return {
            "quiz_id": quiz_id,
            "topic": topic,
            "difficulty": difficulty,
            "questions": persisted_questions
        }

# Singleton instance
_quiz_generator: QuizGenerator | None = None

def get_quiz_generator() -> QuizGenerator:
    global _quiz_generator
    if _quiz_generator is None:
        _quiz_generator = QuizGenerator()
    return _quiz_generator
