import os
import uuid
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_EMBEDDING_MODEL,
    UPLOAD_DIRECTORY,
    MAX_UPLOAD_SIZE_MB,
    ALLOWED_EXTENSIONS
)
from backend.database import init_db, get_db
from backend.parsers import parse_document
from backend.rag.chunker import chunk_document
from backend.rag.vector_store import get_vector_store
from backend.rag.chat import get_chat_service
from backend.assessment.quiz_generator import get_quiz_generator
from backend.assessment.grader import QuizGrader
from backend.assessment.mastery import MasteryManager
from backend.models.schemas import (
    DocumentUploadResponse,
    DocumentSummary,
    ChatRequest,
    ChatResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizGradeRequest,
    QuizGradeResponse,
    MasteryResponse,
    TopicMasteryItem
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("smart_study_portal")

# Initialize database schema
init_db()

# Create FastAPI app
app = FastAPI(
    title="Smart Study Portal API",
    description="Backend API for AI-powered personalized tutoring, RAG study assistant, quizzes, and mastery tracking.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Exception Handlers ----------------- #

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) or "Internal server error occurred."}
    )

# ----------------- Endpoints ----------------- #

@app.get("/api/health")
async def health_check():
    """
    Health check returning system status and model configuration.
    """
    return {
        "status": "ok",
        "service": "Smart Study Portal API",
        "has_gemini_api_key": bool(GEMINI_API_KEY),
        "models": {
            "gemini_model": GEMINI_MODEL,
            "gemini_embedding_model": GEMINI_EMBEDDING_MODEL
        }
    }

@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads, parses, and chunks a study material document (PDF, PPTX, DOCX, TXT),
    storing chunks in ChromaDB and metadata in SQLite.
    """
    filename = file.filename or "uploaded_file"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Read content and enforce size limits
    contents = await file.read()
    file_size = len(contents)
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_UPLOAD_SIZE_MB}MB."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty."
        )

    document_id = str(uuid.uuid4())
    save_filename = f"{document_id}_{filename}"
    file_path = UPLOAD_DIRECTORY / save_filename

    # Save to disk
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        # Parse document
        parsed_doc = parse_document(str(file_path), filename, document_id)
        sections = parsed_doc.get("sections", [])
        
        if not sections:
            # Clean up file
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No readable text found in the uploaded file. Please ensure the document is not an image-only scan or empty."
            )

        # Generate semantic chunks
        chunks = chunk_document(parsed_doc)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to generate semantic chunks from the document content."
            )

        # Store in ChromaDB vector store
        vector_store = get_vector_store()
        vector_store.add_chunks(chunks)

        # Store document record and chunks in SQLite
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO documents (id, filename, file_path, source_type, file_size, total_sections)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (document_id, filename, str(file_path), parsed_doc["source_type"], file_size, len(sections))
            )

            for idx, c in enumerate(chunks):
                meta_json = json.dumps(c.get("metadata", {}))
                p_num = c.get("metadata", {}).get("page") or c.get("metadata", {}).get("slide")
                cursor.execute(
                    """
                    INSERT INTO chunks (chunk_id, document_id, chunk_index, page_or_slide_number, source_type, text, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (c["chunk_id"], document_id, idx, p_num, parsed_doc["source_type"], c["text"], meta_json)
                )

            # Retrieve created timestamp
            cursor.execute("SELECT created_at FROM documents WHERE id = ?", (document_id,))
            created_at = cursor.fetchone()["created_at"]

        summary = DocumentSummary(
            id=document_id,
            filename=filename,
            source_type=parsed_doc["source_type"],
            file_size=file_size,
            total_sections=len(sections),
            created_at=str(created_at)
        )

        return DocumentUploadResponse(
            message=f"Document '{filename}' successfully parsed and indexed into {len(chunks)} semantic chunks.",
            document=summary,
            total_chunks=len(chunks)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded document {filename}: {e}", exc_info=True)
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse and index document: {str(e)}"
        )

@app.get("/api/documents", response_model=List[DocumentSummary])
async def list_documents():
    """
    Returns list of all uploaded and indexed documents.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, source_type, file_size, total_sections, created_at FROM documents ORDER BY created_at DESC")
        rows = cursor.fetchall()
        return [
            DocumentSummary(
                id=r["id"],
                filename=r["filename"],
                source_type=r["source_type"],
                file_size=r["file_size"],
                total_sections=r["total_sections"],
                created_at=str(r["created_at"])
            )
            for r in rows
        ]

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Deletes a document from SQLite, ChromaDB, and disk.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, file_path FROM documents WHERE id = ?", (document_id,))
        doc = cursor.fetchone()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        # Delete from disk
        file_path = Path(doc["file_path"])
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Could not delete file {file_path}: {e}")

        # Delete from vector store
        vector_store = get_vector_store()
        vector_store.delete_document_chunks(document_id)

        # Delete from SQLite (cascades to chunks)
        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))

    return {"message": f"Document '{doc['filename']}' deleted successfully.", "document_id": document_id}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG chat endpoint: retrieves relevant chunks, enforces relevance threshold,
    and returns source-grounded answers with exact citations.
    """
    if not request.question.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question cannot be empty.")

    chat_service = get_chat_service()
    result = chat_service.answer_question(request.question)
    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"]
    )

@app.post("/api/quiz/generate", response_model=QuizGenerateResponse)
async def generate_quiz(request: QuizGenerateRequest):
    """
    Generates topic-specific MCQs grounded in uploaded materials,
    with duplicate prevention and schema validation.
    """
    if not request.topic.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic cannot be empty.")

    quiz_gen = get_quiz_generator()
    try:
        result = quiz_gen.generate_quiz(
            topic=request.topic,
            difficulty=request.difficulty,
            number_of_questions=request.number_of_questions
        )
        return QuizGenerateResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error generating quiz: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Quiz generation error: {str(e)}")

@app.get("/api/quiz/{quiz_id}")
async def get_quiz(quiz_id: str):
    """
    Retrieves quiz questions for a student attempt.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, topic, difficulty, total_questions, created_at FROM quizzes WHERE id = ?", (quiz_id,))
        quiz = cursor.fetchone()
        if not quiz:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found.")

        cursor.execute(
            """
            SELECT id, question_text, options_json, explanation, source_json
            FROM questions
            WHERE quiz_id = ?
            ORDER BY created_at ASC
            """,
            (quiz_id,)
        )
        questions = []
        for q in cursor.fetchall():
            questions.append({
                "id": q["id"],
                "question": q["question_text"],
                "options": json.loads(q["options_json"]),
                "explanation": q["explanation"],
                "source": json.loads(q["source_json"])
            })

        return {
            "quiz_id": quiz["id"],
            "topic": quiz["topic"],
            "difficulty": quiz["difficulty"],
            "total_questions": quiz["total_questions"],
            "created_at": str(quiz["created_at"]),
            "questions": questions
        }

@app.post("/api/quiz/grade", response_model=QuizGradeResponse)
async def grade_quiz(request: QuizGradeRequest):
    """
    Grades an MCQ quiz, records attempt and answers, updates mastery,
    and returns source-grounded feedback.
    """
    try:
        result = QuizGrader.grade_quiz(
            quiz_id=request.quiz_id,
            submitted_answers=request.answers
        )
        return QuizGradeResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Error grading quiz: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Grading error: {str(e)}")

@app.get("/api/mastery", response_model=MasteryResponse)
async def get_mastery():
    """
    Returns student topic mastery records.
    """
    topics_data = MasteryManager.get_all_mastery()
    return MasteryResponse(
        topics=[TopicMasteryItem(**t) for t in topics_data]
    )

if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, PORT
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
