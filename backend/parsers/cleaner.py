import re

def clean_text(text: str) -> str:
    """
    Cleans raw text by normalizing excessive whitespace, Unicode spacing,
    and control characters, while preserving intentional paragraph breaks.
    """
    if not text:
        return ""
    
    # Replace non-breaking spaces and special whitespace characters
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    
    # Replace carriage returns with standard newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Replace multiple horizontal spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    
    # Replace 3 or more consecutive newlines with 2 newlines (preserve paragraph separation)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Strip leading and trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()
    
    return cleaned
