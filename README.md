# Smart Study Portal
### Track D — Personalized Tutoring & Adaptive Learning

Smart Study Portal is an AI-powered learning platform that helps students study from their own course materials. Students can upload documents, ask questions grounded in their notes, generate topic-specific quizzes, receive personalized feedback, and track their performance across topics.

The project combines Retrieval-Augmented Generation (RAG), vector search, automated assessment, and topic mastery tracking to provide a more personalized study experience.

## Key Features

- **Multiformat document ingestion:** Upload PDF, PPTX, PPT, DOCX, and TXT study materials.
- **Source-grounded AI tutor:** Ask questions and receive answers based on retrieved course content, with page or slide citations when available.
- **Out-of-scope handling:** Reject questions when the retriever does not find sufficiently relevant course material.
- **Topic-specific quizzes:** Generate multiple-choice questions at different difficulty levels.
- **Duplicate question prevention:** Check generated questions against previous questions using text similarity.
- **Automatic assessment:** Grade submitted MCQ answers against stored answer keys.
- **Personalized feedback:** Generate feedback on incorrect answers and recommend relevant study material.
- **Topic mastery tracking:** Maintain a mastery estimate based on current and previous quiz scores.
- **Interactive API documentation:** Explore and test backend endpoints through FastAPI's Swagger UI.

## Architecture

```text
                    Student
                       |
                       v
              React + Vite Frontend
                       |
                       v
                 FastAPI Backend
                       |
          +------------+------------+
          |            |            |
          v            v            v
      Document       AI Chat       Quiz
      Upload         Service      Generator
          |            |            |
          v            v            v
       Parsers      Retriever     Validation
          |            |            |
          v            v            v
       Chunking    ChromaDB       SQLite
          |            ^            |
          v            |            v
      Embeddings ------+         Grading
          |                         |
          v                         v
       ChromaDB                 AI Feedback
                                    |
                                    v
                              Topic Mastery
```

### Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, FastAPI, Uvicorn |
| Language model | Google Gemini API |
| Embeddings | Gemini embedding service with local fallback |
| Vector database | ChromaDB |
| Relational database | SQLite |
| Document processing | PyMuPDF, python-docx, python-pptx |
| Testing | Pytest |

## How It Works

### 1. Document Ingestion

When a student uploads a supported document, the backend:

1. Validates the file type and size.
2. Extracts text and available page or slide metadata.
3. Splits extracted text into smaller chunks.
4. Generates embeddings for the chunks.
5. Stores chunk vectors and searchable text in ChromaDB.
6. Stores document records and chunk metadata in SQLite.

The chunking implementation uses a sliding window with a target size of approximately 500 characters and 50 characters of overlap, with boundary handling where possible.

### 2. Retrieval-Augmented Generation (RAG)

When a student asks a question:

1. The question is converted into an embedding.
2. ChromaDB retrieves similar document chunks.
3. The retriever filters results using a similarity threshold.
4. Relevant chunks are added to the prompt with source metadata.
5. Gemini generates an answer using the supplied course context.
6. The backend returns the answer and source information.

If the retriever does not find sufficiently relevant material, the application can return an out-of-scope response instead of generating an unsupported answer.

**Note:** Retrieval thresholds and prompt instructions help reduce unsupported answers, but do not guarantee factual correctness. Citation accuracy depends on the retrieved material and the answer-generation process.

### 3. Quiz Generation

The quiz generator retrieves course content related to the requested topic and asks Gemini to generate multiple-choice questions.

The generated output is checked for expected fields, four options, a valid correct-answer index, explanations, and duplicate questions. Validated questions are stored in SQLite for later grading and review.

### 4. Assessment and Feedback

Student submissions are graded deterministically by comparing selected options with the stored answer key.

After grading, the application can generate personalized feedback based on missed questions, including likely weak areas and study recommendations. A rule-based fallback is available if AI feedback generation fails.

### 5. Topic Mastery Tracking

The application maintains a mastery estimate for each topic.

For subsequent quiz attempts, the update formula is:

\[
M_{\text{new}}=0.70M_{\text{old}}+0.30S_{\text{current}}
\]

Where:

- \(M_{\text{old}}\) is the previous mastery estimate.
- \(S_{\text{current}}\) is the latest quiz score percentage.
- \(M_{\text{new}}\) is the updated mastery estimate.

For the first attempt, mastery is initialized using the current quiz score.

This is a lightweight score-based mastery model, not a complete cognitive or forgetting model.

## Project Structure

```text
smart_study/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── requirements.txt
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── pptx_parser.py
│   │   ├── txt_parser.py
│   │   └── cleaner.py
│   ├── rag/
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   ├── prompts.py
│   │   └── chat.py
│   ├── assessment/
│   │   ├── quiz_generator.py
│   │   ├── grader.py
│   │   ├── feedback.py
│   │   └── mastery.py
│   ├── models/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   └── package.json
├── sample_materials/
├── .gitignore
└── README.md
```

The tree above summarizes the main project components. Refer to the repository for the complete file list.

## Prerequisites

Install the following before running the application:

- Python 3.10 or a version supported by the project's dependencies.
- Node.js and npm.
- A Google Gemini API key for AI-powered features.
- Git, to clone the repository.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Ritik-m-desighn/smart_study.git
cd smart_study
```

If the project is on a different branch, switch to the appropriate branch:

```bash
git checkout ritik
```

### 2. Create and activate a Python virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run the following in the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

Create a `backend/.env` file based on `backend/.env.example`.

Add your own Gemini API key and verify the model names against the values supported by your installed Gemini API configuration.

Example:

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=your_supported_gemini_model
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

Use the environment variable names and paths expected by `backend/config.py`. Do not commit your real `.env` file or API key.

### 5. Start the backend

From the project root:

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend API will be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

### 6. Install and start the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, typically:

`http://localhost:5173`

If the frontend uses a Vite proxy, confirm that its target points to the running backend at `http://127.0.0.1:8000`.

## Demonstration Workflow

For a repeatable demonstration:

1. Start the backend and frontend.
2. Upload a prepared, text-based PDF or presentation containing a few clear concepts.
3. Ask the tutor a question whose answer is explicitly present in the uploaded material.
4. Show the answer and its available page or slide citation.
5. Ask an unrelated question to demonstrate out-of-scope handling.
6. Generate a quiz on a topic from the uploaded material.
7. Submit a mix of correct and incorrect answers.
8. Show the score, answer explanations, and personalized feedback.
9. Open the mastery view to show the updated topic score.

Use a small, known document so the demo stays focused and easy to reproduce.

## Running Tests

From the project root, activate the virtual environment and run:

```bash
python -m pytest backend/tests -v
```

The test suite includes checks for document parsing, metadata preservation, chunking, vector search, RAG responses, out-of-scope handling, quiz validation, duplicate detection, grading, and mastery calculations.

Test results depend on the current code, environment, and API availability. Run the suite before reporting a passing test count. If a test requires Gemini, configure the required API key or update the test to use a controlled mock.

## Security and Limitations

- Keep Gemini credentials in backend environment variables. Never expose API keys in frontend code or commit them to GitHub.
- Keep `.env`, uploaded files, local databases, and generated ChromaDB data out of Git unless they are intentionally prepared, non-sensitive demo assets.
- Uploaded file validation does not replace comprehensive security checks. Review file size limits, parsing errors, and storage handling before deploying publicly.
- Retrieval similarity is not proof that an answer is correct.
- Generated quizzes and AI feedback can contain mistakes and should be checked against the source material.
- The current mastery model uses quiz scores as a simple estimate of topic understanding.
- Scanned PDFs and image-based diagrams may require OCR or additional multimodal processing that is not included in basic text extraction.
- Evaluation with RAGAS, DeepEval, or TruLens should be documented only if it has actually been implemented and run.

## Future Improvements

- Add automated RAG evaluation for answer relevance, groundedness, and retrieval quality.
- Improve citation verification against retrieved source passages.
- Add OCR and image-aware extraction for scanned documents and diagrams.
- Improve learner modelling with question-level skill tracking and spaced repetition.
- Add automated CI checks and more isolated tests using mocked model responses.

## Acknowledgements

Built as a hackathon project for **Track D — Personalized Tutoring & Adaptive Learning**.
