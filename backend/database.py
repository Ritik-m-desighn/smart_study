import sqlite3
import json
from contextlib import contextmanager
from typing import Generator
from backend.config import DATABASE_PATH

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            source_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            total_sections INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Chunks table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            page_or_slide_number INTEGER,
            source_type TEXT,
            text TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents (id) ON DELETE CASCADE
        );
        """)
        
        # Quizzes table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id TEXT PRIMARY KEY,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            total_questions INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Questions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id TEXT PRIMARY KEY,
            quiz_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            question_text TEXT NOT NULL,
            options_json TEXT NOT NULL,
            correct_answer_index INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            source_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        );
        """)
        
        # Quiz attempts table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id TEXT PRIMARY KEY,
            quiz_id TEXT NOT NULL,
            topic TEXT NOT NULL,
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percentage REAL NOT NULL,
            feedback_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes (id) ON DELETE CASCADE
        );
        """)
        
        # Answers table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id TEXT PRIMARY KEY,
            attempt_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            selected_answer INTEGER NOT NULL,
            correct_answer INTEGER NOT NULL,
            is_correct INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (attempt_id) REFERENCES quiz_attempts (id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
        );
        """)
        
        # Topic mastery table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS topic_mastery (
            topic TEXT PRIMARY KEY COLLATE NOCASE,
            previous_mastery REAL DEFAULT 0.0,
            current_score_percentage REAL DEFAULT 0.0,
            updated_mastery REAL DEFAULT 0.0,
            quiz_count INTEGER DEFAULT 0,
            last_attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(document_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_quiz_id ON questions(quiz_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_quiz_id ON quiz_attempts(quiz_id);")
