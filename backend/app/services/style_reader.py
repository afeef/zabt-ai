import pypdf
from pathlib import Path


def parse_pdf(file_path: Path) -> str:
    try:
        text = ""
        reader = pypdf.PdfReader(str(file_path))
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error parsing PDF {file_path}: {e}")
        return ""


def read_style_examples(styles_dir: Path) -> list[str]:
    """Read all PDF style examples and return a list of extracted texts (one per file)."""
    if not styles_dir.exists():
        return []

    examples: list[str] = []
    for pdf_path in sorted(styles_dir.glob("*.pdf")):
        text = parse_pdf(pdf_path)
        if text.strip():
            examples.append(text.strip())
    return examples
