from pathlib import Path
from pypdf import PdfReader
from typing import List

class PDFParser:
    @staticmethod
    def extract_text(file_path: Path) -> str:
        """
        Extracts all text from a PDF file.
        Used for ingesting 'Example Notes' for few-shot prompting.
        """
        reader = PdfReader(str(file_path))
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

    @staticmethod
    def load_examples(examples_dir: Path) -> List[str]:
        """
        Loads all PDF examples from a directory.
        Returns a list of text strings (one per example).
        """
        examples = []
        if not examples_dir.exists():
            return []
            
        for file in examples_dir.glob("*.pdf"):
            try:
                text = PDFParser.extract_text(file)
                if text:
                    examples.append(text)
            except Exception as e:
                print(f"Error parsing {file}: {e}")
        return examples
