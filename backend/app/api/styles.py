# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
import pypdf

router = APIRouter()

STYLES_DIR = Path(os.environ.get("STYLES_DIR", "/media/styles"))  # noqa: env override for non-docker dev
STYLES_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=List[str])
async def upload_style_examples(files: List[UploadFile] = File(...)):
    """
    Upload PDF examples to be used for few-shot prompting.
    """
    saved_files = []
    try:
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                continue
                
            file_location = STYLES_DIR / file.filename
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            saved_files.append(file.filename)
            
        return saved_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[str])
async def list_style_examples():
    """
    List all available style examples.
    """
    if not STYLES_DIR.exists():
        return []
    return [f.name for f in STYLES_DIR.glob("*.pdf")]

def get_all_style_text() -> str:
    """
    Reads all PDF files in the styles directory and returns their text content concatenated.
    Used by the worker to provide few-shot examples to the LLM.
    """
    if not STYLES_DIR.exists():
        return ""
        
    all_text = ""
    for pdf_path in STYLES_DIR.glob("*.pdf"):
        try:
            text = ""
            reader = pypdf.PdfReader(pdf_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            if text.strip():
                all_text += f"\n--- Example Style (from {pdf_path.name}) ---\n{text}\n"
        except Exception as e:
            print(f"Error reading style file {pdf_path}: {e}")
            
    return all_text
