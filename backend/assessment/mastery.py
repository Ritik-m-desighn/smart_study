from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.database import get_db

def calculate_new_mastery(
    old_mastery: Optional[float],
    current_score_percentage: float,
    is_first_attempt: bool
) -> float:
    """
    Computes updated mastery:
    - First attempt: mastery = current_score_percentage
    - Subsequent attempts: new_mastery = (old_mastery * 0.7) + (current_score_percentage * 0.3)
    Clamped strictly between 0 and 100.
    """
    if is_first_attempt or old_mastery is None:
        new_val = current_score_percentage
    else:
        new_val = (old_mastery * 0.7) + (current_score_percentage * 0.3)

    return max(0.0, min(100.0, round(new_val, 1)))

class MasteryManager:
    @staticmethod
    def get_topic_mastery(topic: str) -> Optional[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT topic, previous_mastery, current_score_percentage, updated_mastery, quiz_count, last_attempted_at FROM topic_mastery WHERE topic = ? COLLATE NOCASE",
                (topic.strip(),)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    @staticmethod
    def update_topic_mastery(topic: str, score_percentage: float) -> Dict[str, Any]:
        """
        Updates mastery record for the given topic in SQLite.
        """
        topic_clean = topic.strip()
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT previous_mastery, updated_mastery, quiz_count FROM topic_mastery WHERE topic = ? COLLATE NOCASE",
                (topic_clean,)
            )
            row = cursor.fetchone()

            if row is None:
                # First attempt
                old_mastery = 0.0
                new_mastery = calculate_new_mastery(None, score_percentage, is_first_attempt=True)
                quiz_count = 1
                cursor.execute(
                    """
                    INSERT INTO topic_mastery (topic, previous_mastery, current_score_percentage, updated_mastery, quiz_count, last_attempted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (topic_clean, old_mastery, score_percentage, new_mastery, quiz_count, now_str)
                )
            else:
                old_mastery = float(row["updated_mastery"])
                new_mastery = calculate_new_mastery(old_mastery, score_percentage, is_first_attempt=False)
                quiz_count = int(row["quiz_count"]) + 1
                cursor.execute(
                    """
                    UPDATE topic_mastery
                    SET previous_mastery = ?,
                        current_score_percentage = ?,
                        updated_mastery = ?,
                        quiz_count = ?,
                        last_attempted_at = ?
                    WHERE topic = ? COLLATE NOCASE
                    """,
                    (old_mastery, score_percentage, new_mastery, quiz_count, now_str, topic_clean)
                )

            return {
                "topic": topic_clean,
                "previous_mastery": old_mastery,
                "current_score_percentage": score_percentage,
                "updated_mastery": new_mastery,
                "quiz_count": quiz_count,
                "last_attempted_at": now_str
            }

    @staticmethod
    def get_all_mastery() -> List[Dict[str, Any]]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT topic, previous_mastery, current_score_percentage, updated_mastery, quiz_count, last_attempted_at FROM topic_mastery ORDER BY updated_mastery DESC"
            )
            rows = cursor.fetchall()
            return [
                {
                    "topic": r["topic"],
                    "mastery": r["updated_mastery"],
                    "previous_mastery": r["previous_mastery"],
                    "current_score_percentage": r["current_score_percentage"],
                    "quiz_count": r["quiz_count"],
                    "last_attempted_at": r["last_attempted_at"]
                }
                for r in rows
            ]
