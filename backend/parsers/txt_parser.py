from typing import Dict, Any, List
from backend.parsers.cleaner import clean_text

def parse_txt(file_path: str, filename: str, document_id: str) -> Dict[str, Any]:
    """
    Parses a plain text file into logical sequential sections/pages,
    preserving logical page numbers and metadata.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        raw_text = f.read()

    cleaned = clean_text(raw_text)
    sections: List[Dict[str, Any]] = []

    # If document has explicit form feed page breaks (\x0c)
    if "\x0c" in raw_text:
        pages = raw_text.split("\x0c")
        for i, page_str in enumerate(pages):
            page_clean = clean_text(page_str)
            if page_clean:
                sections.append({
                    "text": page_clean,
                    "page": i + 1
                })
    else:
        # Split by logical blocks (approx 2000-2500 chars) on double newlines
        paragraphs = cleaned.split("\n\n")
        current_page = 1
        current_chunk: List[str] = []
        current_len = 0

        for p in paragraphs:
            p_strip = p.strip()
            if not p_strip:
                continue
            current_chunk.append(p_strip)
            current_len += len(p_strip)

            if current_len >= 2000:
                sections.append({
                    "text": "\n\n".join(current_chunk),
                    "page": current_page
                })
                current_chunk = []
                current_len = 0
                current_page += 1

        if current_chunk:
            sections.append({
                "text": "\n\n".join(current_chunk),
                "page": current_page
            })

    if not sections and cleaned:
        sections.append({
            "text": cleaned,
            "page": 1
        })

    return {
        "document_id": document_id,
        "filename": filename,
        "source_type": "txt",
        "sections": sections
    }
