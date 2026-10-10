import re
from typing import List, Dict, Any

# Approximate 1 token ~= 4 characters in English
DEFAULT_CHUNK_SIZE_CHARS = 500
DEFAULT_OVERLAP_CHARS = 50

def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE_CHARS,
    overlap: int = DEFAULT_OVERLAP_CHARS
) -> List[str]:
    """
    Splits text semantically preferring paragraph boundaries, headings, and sentence ends.
    Uses sliding window with overlap.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between zero and chunk_size - 1.")

    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        max_end = min(start + chunk_size, len(text))
        end = max_end

        if max_end < len(text):
            region = text[start:max_end]
            min_boundary = start + chunk_size // 2
            semantic_matches = list(re.finditer(r"(?<=[.!?])\s+|\n{2,}", region))
            whitespace_matches = list(re.finditer(r"\s+", region))
            matches = semantic_matches or whitespace_matches
            eligible = [
                start + match.start()
                for match in matches
                if start + match.start() >= min_boundary
            ]
            if eligible:
                end = eligible[-1]

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break

        next_start = max(start + 1, end - overlap)
        if overlap:
            whitespace = re.search(r"\s", text[next_start:end])
            if whitespace:
                next_start += whitespace.end()
        while next_start < len(text) and text[next_start].isspace():
            next_start += 1
        start = max(next_start, end if next_start <= start else next_start)

    return chunks

def chunk_document(document: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Chunks a parsed document representation into discrete semantic chunks.
    Ensures that every chunk preserves:
      - chunk_id
      - document_id
      - text
      - metadata (filename, page or slide, source_type)
    """
    document_id = document["document_id"]
    filename = document["filename"]
    source_type = document["source_type"]
    sections = document.get("sections", [])

    all_chunks: List[Dict[str, Any]] = []

    for sec_idx, section in enumerate(sections):
        sec_text = section.get("text", "")
        if not sec_text:
            continue

        page_num = section.get("page")
        slide_num = section.get("slide")

        # Determine location identifier for chunk ID
        if page_num is not None:
            loc_label = f"page{page_num}"
        elif slide_num is not None:
            loc_label = f"slide{slide_num}"
        else:
            loc_label = f"sec{sec_idx + 1}"

        text_pieces = split_text_into_chunks(sec_text)

        for chunk_idx, piece in enumerate(text_pieces):
            chunk_id = f"{document_id}_{loc_label}_chunk{chunk_idx + 1}"

            meta: Dict[str, Any] = {
                "document_id": document_id,
                "filename": filename,
                "source_type": source_type,
                "section_index": sec_idx + 1,
            }

            if page_num is not None:
                meta["page"] = page_num
            if slide_num is not None:
                meta["slide"] = slide_num

            all_chunks.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "text": piece,
                "metadata": meta
            })

    return all_chunks
