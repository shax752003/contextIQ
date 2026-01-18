import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"
CHROMA_DIR = DATA_DIR / "chroma_db"
IMAGE_DIR = DATA_DIR / "extracted/images"
CHUNKS_DIR = DATA_DIR / "chunks"

# Models
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "google/gemma-3-27b-it:free"

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") 
