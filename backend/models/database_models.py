"""
Database model definitions and helper structures for SQLite tables.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class DocumentRecord:
    id: str
    filename: str
    file_path: str
    source_type: str
    file_size: int
    total_sections: int
    created_at: Optional[str] = None

@dataclass
class ChunkRecord:
    chunk_id: str
    document_id: str
    chunk_index: int
    page_or_slide_number: Optional[int]
    source_type: str
    text: str
    metadata_json: str
    created_at: Optional[str] = None

@dataclass
class QuizRecord:
    id: str
    topic: str
    difficulty: str
    total_questions: int
    created_at: Optional[str] = None

@dataclass
class QuestionRecord:
    id: str
    quiz_id: str
    topic: str
    difficulty: str
    question_text: str
    options_json: str
    correct_answer_index: int
    explanation: str
    source_json: str
    created_at: Optional[str] = None

@dataclass
class QuizAttemptRecord:
    id: str
    quiz_id: str
    topic: str
    score: int
    total: int
    percentage: float
    feedback_json: Optional[str] = None
    created_at: Optional[str] = None

@dataclass
class TopicMasteryRecord:
    topic: str
    previous_mastery: float
    current_score_percentage: float
    updated_mastery: float
    quiz_count: int
    last_attempted_at: Optional[str] = None
