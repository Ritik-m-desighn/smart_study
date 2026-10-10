import os
import pymupdf
import pytest
from pathlib import Path
from backend.parsers.pdf_parser import parse_pdf
from backend.rag.chunker import chunk_document, split_text_into_chunks
from backend.rag.vector_store import VectorStore
from backend.rag.retriever import Retriever
from backend.rag.chat import ChatService
from backend.assessment.mastery import calculate_new_mastery, MasteryManager
from backend.assessment.grader import QuizGrader
from backend.assessment.quiz_generator import (
    QuizGenerator,
    _normalize_quiz_question,
    is_duplicate_question,
    jaccard_similarity
)
from backend.rag.prompts import OUT_OF_SCOPE_RESPONSE
from backend.database import init_db

@pytest.fixture(scope="module")
def sample_pdf(tmp_path_factory):
    """
    Creates a small sample 2-page PDF:
    Page 1: "TCP is a connection-oriented protocol."
    Page 2: "UDP is connectionless."
    """
    tmp_dir = tmp_path_factory.mktemp("pdf_data")
    pdf_path = tmp_dir / "sample_networking.pdf"

    doc = pymupdf.open()
    
    # Page 1
    p1 = doc.new_page()
    p1.insert_text((50, 72), "TCP is a connection-oriented protocol.")

    # Page 2
    p2 = doc.new_page()
    p2.insert_text((50, 72), "UDP is connectionless.")

    doc.save(str(pdf_path))
    doc.close()

    return str(pdf_path)


@pytest.fixture(scope="module")
def test_vector_store(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("chroma_test")
    return VectorStore(persist_dir=str(tmp_dir))


# 1. PDF extraction
def test_1_pdf_extraction(sample_pdf):
    parsed = parse_pdf(sample_pdf, "sample_networking.pdf", "doc_test_1")
    assert parsed["document_id"] == "doc_test_1"
    assert parsed["filename"] == "sample_networking.pdf"
    assert parsed["source_type"] == "pdf"
    assert len(parsed["sections"]) == 2
    assert "TCP is a connection-oriented protocol" in parsed["sections"][0]["text"]
    assert "UDP is connectionless" in parsed["sections"][1]["text"]


# 2. Page metadata preservation
def test_2_page_metadata_preservation(sample_pdf):
    parsed = parse_pdf(sample_pdf, "sample_networking.pdf", "doc_test_2")
    sections = parsed["sections"]
    assert sections[0]["page"] == 1
    assert sections[1]["page"] == 2


# 3. Chunk generation
def test_3_chunk_generation(sample_pdf):
    parsed = parse_pdf(sample_pdf, "sample_networking.pdf", "doc_test_3")
    chunks = chunk_document(parsed)
    assert len(chunks) == 2
    
    chunk1 = chunks[0]
    assert chunk1["chunk_id"] == "doc_test_3_page1_chunk1"
    assert chunk1["document_id"] == "doc_test_3"
    assert chunk1["metadata"]["page"] == 1
    assert chunk1["metadata"]["filename"] == "sample_networking.pdf"
    assert "TCP" in chunk1["text"]

    chunk2 = chunks[1]
    assert chunk2["chunk_id"] == "doc_test_3_page2_chunk1"
    assert chunk2["document_id"] == "doc_test_3"
    assert chunk2["metadata"]["page"] == 2
    assert "UDP" in chunk2["text"]

def test_chunk_size_and_overlap_keep_chunks_bounded():
    from backend.rag.chunker import DEFAULT_CHUNK_SIZE_CHARS, DEFAULT_OVERLAP_CHARS

    text = " ".join(f"Sentence {i} describes a networking concept." for i in range(40))
    chunks = split_text_into_chunks(text)

    assert DEFAULT_CHUNK_SIZE_CHARS == 500
    assert DEFAULT_OVERLAP_CHARS == 50
    assert len(chunks) > 1
    assert all(0 < len(chunk) <= DEFAULT_CHUNK_SIZE_CHARS for chunk in chunks)
    assert any(set(chunk.split()) & set(chunks[index + 1].split()) for index, chunk in enumerate(chunks[:-1]))

def test_chunk_size_splits_long_unbroken_text():
    chunks = split_text_into_chunks("x" * 1200)

    assert len(chunks) > 1
    assert all(len(chunk) <= 500 for chunk in chunks)

def test_quiz_question_options_must_be_concise_and_clean():
    valid_question = {
        "question": "Which protocol is connection-oriented?",
        "options": ["A. TCP", "UDP", "File transfer", "Network layer"],
        "correct_answer": 0,
        "explanation": "TCP establishes a connection.",
        "source": {"page": 1}
    }
    invalid_question = {
        **valid_question,
        "options": ["TCP is used for a reliable connection", "UDP", "File transfer", "Network layer"]
    }

    normalized = _normalize_quiz_question(valid_question)
    assert normalized is not None
    assert normalized["options"] == ["TCP", "UDP", "File transfer", "Network layer"]
    assert _normalize_quiz_question(invalid_question) is None


# 4. Vector search
def test_4_vector_search(sample_pdf, test_vector_store):
    parsed = parse_pdf(sample_pdf, "sample_networking.pdf", "doc_test_4")
    chunks = chunk_document(parsed)
    test_vector_store.add_chunks(chunks)

    results = test_vector_store.similarity_search("What is TCP?", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert "TCP" in top["text"]
    assert top["metadata"]["page"] == 1


# 5. RAG citation handling
def test_5_rag_citation_handling(sample_pdf, test_vector_store):
    chat_service = ChatService()
    chat_service.retriever.vector_store = test_vector_store

    response = chat_service.answer_question("What is TCP?")
    assert "answer" in response
    assert "[Page 1]" in response["answer"]
    assert len(response["sources"]) > 0
    assert response["sources"][0]["page"] == 1
    assert response["sources"][0]["filename"] == "sample_networking.pdf"


# 6. Out-of-scope question
def test_6_out_of_scope_question(test_vector_store):
    chat_service = ChatService()
    chat_service.retriever.vector_store = test_vector_store

    response = chat_service.answer_question("What is the capital of France?")
    assert response["answer"] == OUT_OF_SCOPE_RESPONSE
    assert response["sources"] == []


# 7. Quiz JSON validation
def test_7_quiz_json_validation(sample_pdf, test_vector_store):
    init_db()
    quiz_gen = QuizGenerator()
    quiz_gen.retriever.vector_store = test_vector_store

    quiz = quiz_gen.generate_quiz(topic="TCP", difficulty="medium", number_of_questions=3)
    assert "quiz_id" in quiz
    assert quiz["topic"] == "TCP"
    assert len(quiz["questions"]) == 3

    for q in quiz["questions"]:
        assert "question" in q and len(q["question"]) > 5
        assert "options" in q and len(q["options"]) == 4
        assert 0 <= q["correct_answer"] <= 3
        assert "explanation" in q and len(q["explanation"]) > 0
        assert "source" in q


# 8. Duplicate quiz prevention
def test_8_duplicate_quiz_prevention():
    q1 = "What is the primary function of TCP in computer networking?"
    q2 = "What is the main function of TCP in computer networking?"
    q3 = "How does UDP handle connectionless datagram packets?"

    # q1 and q2 are very similar
    assert jaccard_similarity(q1, q2) > 0.65
    assert is_duplicate_question(q2, [q1]) is True

    # q3 is distinct
    assert is_duplicate_question(q3, [q1]) is False


# 9. MCQ grading
def test_9_mcq_grading(sample_pdf, test_vector_store):
    init_db()
    quiz_gen = QuizGenerator()
    quiz_gen.retriever.vector_store = test_vector_store

    quiz = quiz_gen.generate_quiz(topic="TCP", difficulty="medium", number_of_questions=2)
    quiz_id = quiz["quiz_id"]
    q1_correct = quiz["questions"][0]["correct_answer"]
    q2_correct = quiz["questions"][1]["correct_answer"]

    # Student answers: Q1 correct, Q2 wrong
    wrong_q2 = (q2_correct + 1) % 4
    submitted = [q1_correct, wrong_q2]

    grade_result = QuizGrader.grade_quiz(quiz_id, submitted, generate_ai_feedback=False)
    assert grade_result["score"] == 1
    assert grade_result["total"] == 2
    assert grade_result["percentage"] == 50.0
    assert grade_result["questions"][0]["correct"] is True
    assert grade_result["questions"][1]["correct"] is False


# 10. Mastery calculation
def test_10_mastery_calculation():
    # First attempt: mastery = current_score_percentage
    m1 = calculate_new_mastery(old_mastery=None, current_score_percentage=80.0, is_first_attempt=True)
    assert m1 == 80.0

    # Subsequent attempt example from prompt:
    # Old mastery = 70, New quiz score = 90
    # New mastery: 70 * 0.7 + 90 * 0.3 = 49 + 27 = 76%
    m2 = calculate_new_mastery(old_mastery=70.0, current_score_percentage=90.0, is_first_attempt=False)
    assert m2 == 76.0

    # Clamping tests
    m_high = calculate_new_mastery(old_mastery=100.0, current_score_percentage=100.0, is_first_attempt=False)
    assert m_high <= 100.0
    m_low = calculate_new_mastery(old_mastery=0.0, current_score_percentage=0.0, is_first_attempt=False)
    assert m_low >= 0.0
