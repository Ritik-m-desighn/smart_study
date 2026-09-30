import re
from typing import List, Dict, Any

# Approximate 1 token ~= 4 characters in English
DEFAULT_CHUNK_SIZE_CHARS = 2400   # ~600 tokens
DEFAULT_OVERLAP_CHARS = 300       # ~75 tokens

def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE_CHARS,
    overlap: int = DEFAULT_OVERLAP_CHARS
) -> List[str]:
    """
    Splits text semantically preferring paragraph boundaries, headings, and sentence ends.
    Uses sliding window with overlap.
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for para in paragraphs:
        para_clean = para.strip()
        if not para_clean:
            continue

        # If a single paragraph is longer than chunk_size, split by sentences
        if len(para_clean) > chunk_size:
            # First flush what we have
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_length = 0

            sentences = re.split(r"(?<=[.!?])\s+", para_clean)
            sub_chunk: List[str] = []
            sub_len = 0
            for sent in sentences:
                sent_clean = sent.strip()
                if not sent_clean:
                    continue
                if sub_len + len(sent_clean) > chunk_size and sub_chunk:
                    chunks.append(" ".join(sub_chunk))
                    # Compute overlap from trailing sentences
                    overlap_str = " ".join(sub_chunk)
                    if len(overlap_str) > overlap:
                        overlap_tail = overlap_str[-overlap:]
                        sub_chunk = [overlap_tail, sent_clean]
                        sub_len = len(overlap_tail) + len(sent_clean)
                    else:
                        sub_chunk = [sent_clean]
                        sub_len = len(sent_clean)
                else:
                    sub_chunk.append(sent_clean)
                    sub_len += len(sent_clean) + 1

            if sub_chunk:
                chunks.append(" ".join(sub_chunk))
            continue

        if current_length + len(para_clean) > chunk_size and current_chunk:
            full_chunk_text = "\n\n".join(current_chunk)
            chunks.append(full_chunk_text)

            # Overlap: keep last part of previous chunk
            if len(full_chunk_text) > overlap:
                tail = full_chunk_text[-overlap:]
                current_chunk = [tail, para_clean]
                current_length = len(tail) + len(para_clean) + 2
            else:
                current_chunk = [para_clean]
                current_length = len(para_clean)
        else:
            current_chunk.append(para_clean)
            current_length += len(para_clean) + 2

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

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
