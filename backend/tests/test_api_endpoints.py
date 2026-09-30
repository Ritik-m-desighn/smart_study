import pytest
import io
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "models" in data
    assert "has_gemini_api_key" in data

def test_api_documents_list():
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_api_chat_empty_handling():
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 422 or response.status_code == 400

def test_api_mastery_get():
    response = client.get("/api/mastery")
    assert response.status_code == 200
    data = response.json()
    assert "topics" in data
    assert isinstance(data["topics"], list)

def test_api_upload_txt_file():
    txt_content = b"HTTP is a stateless application layer protocol used for distributed, collaborative, hypermedia information systems."
    response = client.post(
        "/api/documents/upload",
        files={"file": ("web_protocols.txt", io.BytesIO(txt_content), "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "document" in data
    assert data["document"]["filename"] == "web_protocols.txt"
    doc_id = data["document"]["id"]

    # Test Chat querying this new document
    chat_resp = client.post("/api/chat", json={"question": "What is HTTP?"})
    assert chat_resp.status_code == 200
    chat_data = chat_resp.json()
    assert "answer" in chat_data
    assert len(chat_data["sources"]) > 0

    # Test Delete
    del_resp = client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 200
