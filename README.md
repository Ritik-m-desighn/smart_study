# Smart Study Portal (Track D — Personalized Tutoring & Adaptive Learning)

An AI-powered adaptive study portal for students to upload course materials (PDF, PPTX/PPT, DOCX, TXT), receive source-grounded answers with exact citations (e.g. `[Page 12]` or `[Slide 5]`), generate topic-specific quizzes with duplicate prevention, receive personalized AI diagnostic feedback, and track topic mastery with an adaptive learning curve.

---

## Architecture Overview

```
smart-study-portal/
├── backend/
│   ├── main.py                  # FastAPI application with all REST API endpoints
│   ├── config.py                # Environment configuration and paths
│   ├── database.py              # SQLite schema, connection manager, tables
│   ├── parsers/
│   │   ├── __init__.py          # Format dispatcher
│   │   ├── pdf_parser.py        # PyMuPDF page-by-page extractor
│   │   ├── docx_parser.py       # python-docx paragraph/table extractor
│   │   ├── pptx_parser.py       # python-pptx slide-by-slide extractor
│   │   ├── txt_parser.py        # Plaintext sequential section parser
│   │   └── cleaner.py           # Whitespace and unicode normalization
│   ├── rag/
│   │   ├── chunker.py           # Semantic chunker with metadata preservation
│   │   ├── embeddings.py        # Gemini embedding service with fallback capability
│   │   ├── vector_store.py      # ChromaDB persistent cosine vector store
│   │   ├── retriever.py         # Relevance thresholding & out-of-scope detection
│   │   ├── prompts.py           # System instructions & strict grounding prompts
│   │   └── chat.py              # RAG chat pipeline with citation extraction
│   ├── assessment/
│   │   ├── quiz_generator.py    # Structured JSON quiz generator & duplicate prevention
│   │   ├── grader.py            # Deterministic MCQ grading & attempt tracking
│   │   ├── feedback.py          # Grounded AI diagnostic feedback
│   │   └── mastery.py           # Per-topic exponential moving average mastery
│   ├── models/
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   └── database_models.py   # Database record dataclasses
│   ├── tests/
│   │   ├── conftest.py          # Pytest setup
│   │   ├── test_study_portal.py # 10 unit test suites covering all track requirements
│   │   └── test_api_endpoints.py# Integration tests for FastAPI endpoints
│   ├── uploads/                 # Uploaded files directory
│   ├── chroma_db/               # Persistent ChromaDB vector database
│   ├── .env.example             # Backend environment template
│   ├── .env                     # Local environment settings
│   └── requirements.txt         # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      # Navigation sidebar with Track D badge
│   │   │   └── Header.jsx       # Status header & Gemini model indicator
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx# Stats, mastery summary, document preview
│   │   │   ├── UploadPage.jsx   # Drag & drop upload, progress, document list
│   │   │   ├── ChatPage.jsx     # AI Tutor Q&A with exact citations & sources
│   │   │   ├── QuizPage.jsx     # Topic/difficulty selector, interactive MCQ quiz
│   │   │   ├── ResultsPage.jsx  # Score, answer breakdown, AI tutor feedback
│   │   │   └── MasteryPage.jsx  # Mastery progress bars & formula breakdown
│   │   ├── services/
│   │   │   └── api.js           # Axios API client
│   │   ├── App.jsx              # Main routing and global state
│   │   ├── index.css            # Clean responsive design system
│   │   └── main.jsx             # React entrypoint
│   ├── vite.config.js           # Vite configuration with /api backend proxy
│   └── package.json
├── sample_materials/
│   ├── computer_networks.pdf    # Multi-page test PDF (TCP, UDP, HTTP)
│   └── networking_slides.pptx   # Multi-slide test PPTX (Routing, DNS)
├── .gitignore
└── README.md
```

---

## Key Features

1. **Document Parsing with Metadata Preservation**:
   - **PDF**: Page-by-page text extraction with `pymupdf` preserving page numbers (1-indexed).
   - **PPTX/PPT**: Slide-by-slide text and shape extraction with `python-pptx` preserving slide numbers and titles.
   - **DOCX**: Paragraphs and tables with section pagination.
   - **TXT**: Sequential logical chunking.
2. **Semantic Chunking**:
   - Sliding window (~600 tokens) with ~75 tokens overlap.
   - Every chunk retains `chunk_id`, `document_id`, `text`, and source metadata (`page` or `slide`).
3. **Modular Embeddings & ChromaDB Vector Store**:
   - Uses Google Gemini embeddings (`gemini-embedding-001`) with automatic deterministic local vector fallback for test environments.
   - Persistent ChromaDB collection using cosine similarity.
4. **Strict RAG Pipeline & Out-of-Scope Protection**:
   - Two layers of protection:
     - **Retrieval-level**: Filters by relevance threshold. If no chunks meet the threshold, returns *"This question is outside the scope of the uploaded course material."* without making an LLM call.
     - **Prompt-level**: Strict system instruction forbidding outside knowledge or fabricated citations.
   - Cites exact sources using `[Page X]` or `[Slide X]`.
5. **Topic-Specific Quiz Generation & Duplicate Prevention**:
   - Generates 5 MCQs per topic at specified difficulty (easy, medium, hard).
   - Retrieves historical questions from SQLite and excludes them via prompt and Python token-similarity checks.
   - Validates JSON output strictly.
6. **Deterministic MCQ Grading & AI Diagnostic Feedback**:
   - Compares answers directly against answer key without LLM hallucination.
   - Identifies incorrect questions, diagnoses misconceptions, and generates source-grounded study recommendations.
7. **Per-Topic Mastery Tracking**:
   - Adaptive formula:
     $$\text{new\_mastery} = (\text{old\_mastery} \times 0.70) + (\text{current\_score\_percentage} \times 0.30)$$
   - First attempt: $\text{mastery} = \text{current\_score\_percentage}$.
   - Clamped strictly between 0% and 100%.

---

## Windows Setup Instructions (PowerShell)

### Step 1: Clone / Navigate to Project Directory
```powershell
cd c:\Users\htc\Desktop\smart-study-portal
```

### Step 2: Create Python Virtual Environment
```powershell
python -m venv backend\venv
```

### Step 3: Activate Virtual Environment
```powershell
backend\venv\Scripts\Activate.ps1
```

*(If PowerShell script execution is restricted on your machine, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 4: Install Backend Dependencies
```powershell
pip install --upgrade pip
pip install -r backend\requirements.txt
```

### Step 5: Configure `.env`
In `backend/.env`, paste your Google Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
HOST=0.0.0.0
PORT=8000
DEBUG=True
CHROMA_PERSIST_DIRECTORY=chroma_db
SIMILARITY_THRESHOLD=0.15
TOP_K_CHUNKS=4
MAX_UPLOAD_SIZE_MB=25
UPLOAD_DIRECTORY=uploads
```

### Step 6: Start FastAPI Backend
Open a PowerShell terminal and run:
```powershell
cd c:\Users\htc\Desktop\smart-study-portal
backend\venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
Backend API will be running at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.

### Step 7: Install Frontend Dependencies & Start React UI
Open a **second** PowerShell terminal:
```powershell
cd c:\Users\htc\Desktop\smart-study-portal\frontend
npm install
npm run dev
```
The React frontend dashboard will start at `http://localhost:5173`.

### Step 8: Open Application & Test Flow
1. Open your browser to `http://localhost:5173`.
2. **Upload a Test Document**:
   - Go to the **Upload Materials** tab.
   - Upload the provided sample document: `sample_materials\computer_networks.pdf` (or `networking_slides.pptx`).
   - The system parses the document, creates chunks, and stores embeddings in ChromaDB.
3. **Ask a Question (AI Tutor)**:
   - Go to the **AI Tutor** tab.
   - Ask: `"What is TCP?"`
   - Notice the grounded response with citations: e.g. `TCP is a connection-oriented protocol. [Page 1]`, and the source card showing `computer_networks.pdf — Page 1`.
   - Ask an out-of-scope question: `"What is the capital of France?"`
   - Notice the retrieval-level refusal: *"This question is outside the scope of the uploaded course material."*
4. **Generate & Take a Quiz**:
   - Go to the **Take Quiz** tab.
   - Enter topic `"TCP"`, select `"Medium"` difficulty, and click **Generate Quiz**.
   - Answer the MCQs and click **Submit Quiz**.
   - View your score percentage, question breakdown, and personalized AI feedback with grounded study advice.
5. **View Mastery**:
   - Check the **Topic Mastery** tab to see your updated mastery percentage calculated via the adaptive formula.

---

## Running Automated Tests

Run the full automated test suite (all 15 tests covering PDF extraction, page metadata, chunking, vector search, RAG citations, out-of-scope refusal, quiz generation, duplicate prevention, grading, mastery, and API endpoints):

```powershell
cd c:\Users\htc\Desktop\smart-study-portal
backend\venv\Scripts\pytest backend\tests -v
```

All 15 tests will execute and pass.

---

## Security Notes
- The `GEMINI_API_KEY` is loaded exclusively inside `backend/config.py` on the server and is **never** exposed to the React client.
- Uploaded file extensions are strictly validated (`.pdf`, `.docx`, `.pptx`, `.ppt`, `.txt`).
- File size limits (25MB) are enforced before reading into memory.
- Uploaded files are not executed.
