import uuid
import json
from typing import List, Dict, Any, Optional
from backend.database import get_db
from backend.assessment.mastery import MasteryManager

class QuizGrader:
    @staticmethod
    def grade_quiz(
        quiz_id: str,
        submitted_answers: List[int],
        generate_ai_feedback: bool = True
    ) -> Dict[str, Any]:
        """
        Grades an MCQ quiz by direct deterministic comparison with stored answer keys.
        Stores the attempt, individual question answers, and updates topic mastery.
        """
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Fetch quiz
            cursor.execute("SELECT id, topic, difficulty, total_questions FROM quizzes WHERE id = ?", (quiz_id,))
            quiz_row = cursor.fetchone()
            if not quiz_row:
                raise ValueError(f"Quiz with ID '{quiz_id}' not found.")

            topic = quiz_row["topic"]

            # Fetch questions in order
            cursor.execute(
                """
                SELECT id, question_text, options_json, correct_answer_index, explanation, source_json
                FROM questions
                WHERE quiz_id = ?
                ORDER BY created_at ASC
                """,
                (quiz_id,)
            )
            question_rows = cursor.fetchall()

        if not question_rows:
            raise ValueError(f"No questions found for quiz '{quiz_id}'.")

        total = len(question_rows)
        score = 0
        graded_questions: List[Dict[str, Any]] = []
        incorrect_items: List[Dict[str, Any]] = []

        for idx, q_row in enumerate(question_rows):
            q_id = q_row["id"]
            correct_idx = int(q_row["correct_answer_index"])
            explanation = q_row["explanation"]
            
            try:
                source = json.loads(q_row["source_json"])
            except Exception:
                source = {}

            try:
                options = json.loads(q_row["options_json"])
            except Exception:
                options = []

            # Selected answer matching index
            selected_idx = submitted_answers[idx] if idx < len(submitted_answers) else -1
            is_correct = (selected_idx == correct_idx)

            if is_correct:
                score += 1
            else:
                incorrect_items.append({
                    "question_id": q_id,
                    "question": q_row["question_text"],
                    "selected_option": options[selected_idx] if 0 <= selected_idx < len(options) else "None",
                    "correct_option": options[correct_idx] if 0 <= correct_idx < len(options) else "Unknown",
                    "explanation": explanation,
                    "source": source
                })

            graded_questions.append({
                "question_id": q_id,
                "correct": is_correct,
                "selected_answer": selected_idx,
                "correct_answer": correct_idx,
                "explanation": explanation,
                "source": source
            })

        percentage = round((score / total) * 100, 1) if total > 0 else 0.0

        # Update topic mastery
        mastery_result = MasteryManager.update_topic_mastery(topic, percentage)

        # AI Feedback generation for incorrect answers
        feedback = None
        if generate_ai_feedback:
            try:
                from backend.assessment.feedback import generate_feedback
                feedback = generate_feedback(topic, incorrect_items)
            except Exception as e:
                feedback = {
                    "summary": f"You scored {score}/{total} ({percentage}%). Review the questions you missed.",
                    "weak_topics": [topic] if percentage < 70 else [],
                    "common_misconceptions": [],
                    "study_recommendations": []
                }

        # Store quiz attempt and answers in DB
        attempt_id = str(uuid.uuid4())
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO quiz_attempts (id, quiz_id, topic, score, total, percentage, feedback_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (attempt_id, quiz_id, topic, score, total, percentage, json.dumps(feedback) if feedback else None)
            )

            for gq in graded_questions:
                cursor.execute(
                    """
                    INSERT INTO answers (id, attempt_id, question_id, selected_answer, correct_answer, is_correct)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        attempt_id,
                        gq["question_id"],
                        gq["selected_answer"],
                        gq["correct_answer"],
                        1 if gq["correct"] else 0
                    )
                )

        return {
            "attempt_id": attempt_id,
            "quiz_id": quiz_id,
            "topic": topic,
            "score": score,
            "total": total,
            "percentage": percentage,
            "questions": graded_questions,
            "feedback": feedback,
            "updated_mastery": mastery_result.get("updated_mastery")
        }
