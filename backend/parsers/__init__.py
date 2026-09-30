import os
from typing import Dict, Any
from backend.parsers.pdf_parser import parse_pdf
from backend.parsers.docx_parser import parse_docx
from backend.parsers.pptx_parser import parse_pptx
from backend.parsers.txt_parser import parse_txt

def parse_document(file_path: str, filename: str, document_id: str) -> Dict[str, Any]:
    """
    Dispatcher to parse supported document formats into the unified document representation.
    """
    ext = os.path.splitext(filename)[1].lower()
    
    if ext == ".pdf":
        return parse_pdf(file_path, filename, document_id)
    elif ext in [".pptx", ".ppt"]:
        return parse_pptx(file_path, filename, document_id)
    elif ext == ".docx":
        return parse_docx(file_path, filename, document_id)
    elif ext == ".txt":
        return parse_txt(file_path, filename, document_id)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
