import os
from pathlib import Path
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip()

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Storage Directories
UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", str(BASE_DIR / "uploads")))
CHROMA_PERSIST_DIRECTORY = Path(os.getenv("CHROMA_PERSIST_DIRECTORY", str(BASE_DIR / "chroma_db")))
DATABASE_PATH = BASE_DIR / "study_portal.db"

# Ensure directories exist
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)

# Constraints and Defaults
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".ppt", ".txt"}

# RAG Relevance Settings
# Chroma cosine distance = 1 - cosine_similarity. Lower distance means higher similarity.
# Threshold can be applied as similarity or distance.
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.15"))
TOP_K_CHUNKS = int(os.getenv("TOP_K_CHUNKS", "4"))
