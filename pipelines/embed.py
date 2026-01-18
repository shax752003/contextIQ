import json
from pathlib import Path
from typing import List, Dict
from app.config import CHUNKS_DIR, CHROMA_DIR
from app.retrieval import get_vectorstore
from app.utils import load_chunks

def build_vector_index():
    print("--- Starting Embedding & Indexing ---")

    # Idempotency check
    if (CHROMA_DIR / "chroma.sqlite3").exists():
        print(f"Vector store already exists at {CHROMA_DIR}. Skipping.")
        return
    
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    
    text_chunks = load_chunks(CHUNKS_DIR / "docling_text_chunks.json")
    table_chunks = load_chunks(CHUNKS_DIR / "table_chunks.json")
    ocr_chunks = load_chunks(CHUNKS_DIR / "ocr_chunks.json")
    image_chunks = load_chunks(CHUNKS_DIR / "image_chunks.json")

    print("Text chunks :", len(text_chunks))
    print("Table chunks:", len(table_chunks))
    print("OCR chunks  :", len(ocr_chunks))
    print("Image chunks:", len(image_chunks))

    documents = []
    metadatas = []
    ids = []

    all_text_chunks = text_chunks + table_chunks + ocr_chunks
    
    for chunk in all_text_chunks:
        documents.append(chunk["content"])
        metadatas.append({
            "source": chunk["source"],
            "type": chunk["type"],
            "page": chunk.get("page"),
            "modality": chunk.get("modality", "text")
        })
        ids.append(chunk["chunk_id"])

    print("total documents to embed:", len(documents))
    
    if not documents:
        print("No documents to index.")
        return

    vectordb = get_vectorstore()
    
    # Batch adding 
    vectordb.add_texts(
        texts=documents,
        metadatas=metadatas,
        ids=ids
    )

    # Persist if needed (older chroma versions)
    # vectordb.persist() 
    print("ChromaDB updated")

    with open(CHROMA_DIR / "image_metadata.json", "w") as f:
        json.dump(image_chunks, f, indent=2)
    
    print("Image metadata saved")

if __name__ == "__main__":
    build_vector_index()
