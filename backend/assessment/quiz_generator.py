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
        if not relevant_chunks:
            # Try searching with fallback top chunks or all available chunks
            raw = self.retriever.vector_store.similarity_search(topic, top_k=6)
            relevant_chunks = raw if raw else []

        if not relevant_chunks:
            raise ValueError(f"No course material found relevant to topic '{topic}'. Please upload study materials first.")

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
                        # Filter duplicates using Python similarity
                        for q in parsed["questions"]:
                            q_text = q.get("question", "")
                            if not is_duplicate_question(q_text, existing_questions):
                                questions_data.append(q)
            except Exception as e:
                logger.error(f"Gemini Quiz Generation failed: {e}. Falling back to grounded generator.")

        # 4. Fallback generator if Gemini was unavailable or returned insufficient questions
        if len(questions_data) < number_of_questions:
            fallback_qs = self._generate_grounded_fallback(
                topic, difficulty, number_of_questions - len(questions_data), relevant_chunks, existing_questions
            )
            questions_data.extend(fallback_qs)

        # Truncate to exact number of questions
        questions_data = questions_data[:number_of_questions]

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

    def _generate_grounded_fallback(
        self,
        topic: str,
        difficulty: str,
        count: int,
        chunks: List[Dict[str, Any]],
        existing_questions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Creates well-formed, source-grounded MCQs directly from chunk text
        for offline testing or when the model quota is reached.
        """
        fallback_qs = []
        for i in range(count):
            chunk = chunks[i % len(chunks)]
            meta = chunk.get("metadata", {})
            text = chunk.get("text", "")
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
            sentence = sentences[i % len(sentences)] if sentences else f"{topic} is an essential concept."

            # Construct question
            question_text = f"According to the course material on {topic}, which of the following statements is true?"
            if is_duplicate_question(question_text, existing_questions):
                question_text = f"Regarding {topic} (Concept #{len(existing_questions) + i + 1}), which statement is correct?"

            correct_option = sentence
            distractor1 = f"It is completely unrelated to {topic}."
            distractor2 = f"It operates in the opposite manner described in the notes."
            distractor3 = "None of the provided concepts apply."

            src: Dict[str, Any] = {"filename": meta.get("filename", "Course Material")}
            if "page" in meta:
                src["page"] = meta["page"]
            if "slide" in meta:
                src["slide"] = meta["slide"]

            fallback_qs.append({
                "question": question_text,
                "options": [correct_option, distractor1, distractor2, distractor3],
                "correct_answer": 0,
                "explanation": f"Grounded directly in {src.get('filename')}: '{sentence}'",
                "source": src,
                "topic": topic,
                "difficulty": difficulty
            })

        return fallback_qs

# Singleton instance
_quiz_generator: QuizGenerator | None = None

def get_quiz_generator() -> QuizGenerator:
    global _quiz_generator
    if _quiz_generator is None:
        _quiz_generator = QuizGenerator()
    return _quiz_generator
