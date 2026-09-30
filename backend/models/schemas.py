from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# ----------------- Document Schemas ----------------- #

class DocumentSection(BaseModel):
    text: str
    page: Optional[int] = None
    slide: Optional[int] = None

class DocumentRepresentation(BaseModel):
    document_id: str
    filename: str
    source_type: str
    sections: List[Dict[str, Any]]

class DocumentSummary(BaseModel):
    id: str
    filename: str
    source_type: str
    file_size: int
    total_sections: int
    created_at: str

class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentSummary
    total_chunks: int

# ----------------- Chunk Schemas ----------------- #

class ChunkMetadata(BaseModel):
    filename: str
    document_id: str
    page: Optional[int] = None
    slide: Optional[int] = None
    source_type: str

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    metadata: Dict[str, Any]

# ----------------- Chat / RAG Schemas ----------------- #

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question asked by student")

class SourceCitation(BaseModel):
    filename: str
    page: Optional[int] = None
    slide: Optional[int] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation] = Field(default_factory=list)

# ----------------- Quiz Schemas ----------------- #

class QuizGenerateRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="Topic for the quiz")
    difficulty: str = Field(default="medium", description="Difficulty level: easy, medium, hard")
    number_of_questions: int = Field(default=5, ge=1, le=10, description="Number of questions to generate")

class QuestionSource(BaseModel):
    filename: Optional[str] = None
    page: Optional[int] = None
    slide: Optional[int] = None

class QuizQuestion(BaseModel):
    id: Optional[str] = None
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4)
    correct_answer: int = Field(..., ge=0, le=3)
    explanation: str
    source: QuestionSource
    topic: Optional[str] = None
    difficulty: Optional[str] = None

class QuizGenerateResponse(BaseModel):
    quiz_id: str
    topic: str
    difficulty: str
    questions: List[QuizQuestion]

# ----------------- Grading Schemas ----------------- #

class QuizGradeRequest(BaseModel):
    quiz_id: str
    answers: List[int]

class GradedQuestion(BaseModel):
    question_id: str
    correct: bool
    selected_answer: int
    correct_answer: int
    explanation: str
    source: QuestionSource

class QuizGradeResponse(BaseModel):
    attempt_id: str
    quiz_id: str
    topic: str
    score: int
    total: int
    percentage: float
    questions: List[GradedQuestion]
    feedback: Optional[Dict[str, Any]] = None
    updated_mastery: Optional[float] = None

# ----------------- Mastery Schemas ----------------- #

class TopicMasteryItem(BaseModel):
    topic: str
    mastery: float
    previous_mastery: Optional[float] = None
    current_score_percentage: Optional[float] = None
    quiz_count: Optional[int] = None
    last_attempted_at: Optional[str] = None

class MasteryResponse(BaseModel):
    topics: List[TopicMasteryItem]
