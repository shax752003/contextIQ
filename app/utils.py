import json
from pathlib import Path
from typing import List, Dict

def load_chunks(path: Path) -> List[Dict]:
    """
    Load JSON chunks from a file.
    
    Args:
        path (Path): Path to the JSON file containing chunks.
        
    Returns:
        List[Dict]: List of chunk dictionaries.
    """
    if not path.exists():
        return []
        
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def clean_text(text: str) -> str:
    """
    Basic text cleaning utility.
    """
    if not text:
        return ""
    return text.strip()

def save_json(data: dict, path: Path):
    """
    Save dictionary to JSON file.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# PDF Helpers
import magic
import fitz
import os

def is_pdf(path: Path) -> bool:
    try:
        t = magic.from_file(str(path), mime=True)
        return t == "application/pdf"
    except Exception as e:
        print(f"Error checking mime type for {path}: {e}")
        return False

def extract_pdf_metadata(pdf_path: Path) -> dict:
    try:
        doc = fitz.open(pdf_path)
        meta = doc.metadata
        info = {
            "file_name": pdf_path.name,
            "path": str(pdf_path),
            "pages": len(doc),
            "title": meta.get("title"),
            "author": meta.get("author"),
            "filesize_kb": round(os.path.getsize(pdf_path) / 1024, 2)
        }
        doc.close()
        return info
    except Exception as e:
        return {"file_name": pdf_path.name, "error": str(e)}
