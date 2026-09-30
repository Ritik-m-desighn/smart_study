from pptx import Presentation
from typing import Dict, Any, List
from backend.parsers.cleaner import clean_text

def parse_pptx(file_path: str, filename: str, document_id: str) -> Dict[str, Any]:
    """
    Parses a PPTX / PPT presentation slide by slide using python-pptx.
    Preserves slide numbers (1-indexed), extracts text from text boxes, tables,
    and shapes, and highlights slide titles when available.
    """
    prs = Presentation(file_path)
    sections: List[Dict[str, Any]] = []

    for slide_index, slide in enumerate(prs.slides):
        slide_num = slide_index + 1
        slide_texts: List[str] = []

        # Check for title shape first
        if slide.shapes.title and slide.shapes.title.text:
            title_text = slide.shapes.title.text.strip()
            if title_text:
                slide_texts.append(f"Title: {title_text}")

        # Extract text from other shapes
        for shape in slide.shapes:
            if shape == slide.shapes.title:
                continue
            
            # Text frames (text boxes, shapes with text)
            if shape.has_text_frame:
                frame_text = shape.text.strip()
                if frame_text:
                    slide_texts.append(frame_text)
            
            # Tables inside slides
            elif shape.has_table:
                table_rows = []
                for row in shape.table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_cells:
                        table_rows.append(" | ".join(row_cells))
                if table_rows:
                    slide_texts.append("\n".join(table_rows))

        combined_text = "\n\n".join(slide_texts)
        cleaned = clean_text(combined_text)
        if cleaned:
            sections.append({
                "text": cleaned,
                "slide": slide_num
            })

    return {
        "document_id": document_id,
        "filename": filename,
        "source_type": "pptx",
        "sections": sections
    }
