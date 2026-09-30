import pymupdf
from typing import Dict, Any, List
from backend.parsers.cleaner import clean_text

def parse_pdf(file_path: str, filename: str, document_id: str) -> Dict[str, Any]:
    """
    Parses a PDF file page by page using PyMuPDF.
    Preserves page numbers (1-indexed), ignores empty pages,
    normalizes excessive whitespace, and preserves headings.
    """
    doc = pymupdf.open(file_path)
    sections: List[Dict[str, Any]] = []

    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            page_num = page_index + 1
            raw_text = page.get_text("text")
            
            cleaned = clean_text(raw_text)
            if not cleaned:
                continue

            sections.append({
                "text": cleaned,
                "page": page_num
            })
    finally:
        doc.close()

    return {
        "document_id": document_id,
        "filename": filename,
        "source_type": "pdf",
        "sections": sections
    }
