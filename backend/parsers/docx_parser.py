from docx import Document
from typing import Dict, Any, List
from backend.parsers.cleaner import clean_text

def parse_docx(file_path: str, filename: str, document_id: str) -> Dict[str, Any]:
    """
    Parses a DOCX document extracting paragraphs and tables.
    Divides content into logical sections/pages preserving page numbers
    and extracting document-level metadata.
    """
    doc = Document(file_path)
    sections: List[Dict[str, Any]] = []

    # Gather core properties if available
    metadata: Dict[str, Any] = {}
    try:
        props = doc.core_properties
        if props.title:
            metadata["title"] = props.title
        if props.author:
            metadata["author"] = props.author
    except Exception:
        pass

    current_page = 1
    current_texts: List[str] = []
    char_count = 0

    def flush_section():
        nonlocal current_texts, current_page, char_count
        if current_texts:
            full_text = "\n\n".join(current_texts)
            cleaned = clean_text(full_text)
            if cleaned:
                sections.append({
                    "text": cleaned,
                    "page": current_page
                })
            current_texts = []
            char_count = 0
            current_page += 1

    # Iterate through paragraphs
    for p in doc.paragraphs:
        # Check for explicit page break in runs
        has_page_break = any(
            "w:br" in r._r.xml and 'w:type="page"' in r._r.xml
            for r in p.runs
        ) if hasattr(p, "runs") else False

        if has_page_break and current_texts:
            flush_section()

        text = p.text.strip()
        if text:
            # Preserve headings formatting
            if p.style and p.style.name and p.style.name.startswith("Heading"):
                current_texts.append(f"## {text}")
            else:
                current_texts.append(text)
            char_count += len(text)

        # Approximate logical page boundary if paragraph text exceeds ~2500 characters
        if char_count > 2500:
            flush_section()

    # Iterate through tables
    for table in doc.tables:
        table_rows = []
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                table_rows.append(" | ".join(cells))
        if table_rows:
            table_text = "\n".join(table_rows)
            current_texts.append(table_text)
            char_count += len(table_text)

        if char_count > 2500:
            flush_section()

    # Flush any remaining text
    flush_section()

    # Fallback if no sections were created
    if not sections and current_texts:
        sections.append({
            "text": clean_text("\n\n".join(current_texts)),
            "page": 1
        })

    return {
        "document_id": document_id,
        "filename": filename,
        "source_type": "docx",
        "metadata": metadata,
        "sections": sections
    }
