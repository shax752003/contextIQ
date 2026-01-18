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
