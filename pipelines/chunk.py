import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import DATA_DIR, CHUNKS_DIR, EXTRACTED_DIR
import app.config as config
from app.embeddings import get_embedding_model

CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
JSON_DIR = EXTRACTED_DIR / "json"
TABLE_DIR = EXTRACTED_DIR / "tables"
IMAGE_DIR = EXTRACTED_DIR / "images"
OCR_DIR = EXTRACTED_DIR / "ocr"

# Docling Chunking
def load_docling_json(jsonpath: Path) -> Dict:
    with open(jsonpath, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_paragraphs(docling_json: Dict) -> List[Dict]:
    texts_data = docling_json.get("texts", [])
    paragraphs = []
    for text_element in texts_data:
        text = text_element.get("text", "").strip()
        if len(text) > 20:
            provenence = text_element.get("prov")
            page_no = None
            if provenence and isinstance(provenence, list) and len(provenence) > 0:
                page_no = provenence[0].get("page_no")
            
            content_layer = text_element.get("content_layer")
            if content_layer in ["body", "unspecified"] and page_no is not None:
                paragraphs.append({"text": text, "page": page_no})
    return paragraphs

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def chunk_docling_json(json_path: Path) -> List[Dict]:
    raw = load_docling_json(json_path)
    paragraphs = extract_paragraphs(raw)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE, 
        chunk_overlap=config.CHUNK_OVERLAP, 
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    embedding_model = get_embedding_model()

    chunks = []
    for para in paragraphs:
        splits = text_splitter.split_text(para["text"])
        for s in splits:
            chunks.append({"text": s, "page": para["page"]})
    
    if not chunks:
        return []

    # Semantic merge
    texts = []
    def normalize_text(t: str) -> str:
        return " ".join(t.lower().split())

    for c in chunks:
        texts.append(normalize_text(c["text"]))

    embeddings = embedding_model.embed_documents(texts)
    final_chunk = []
    buffer = chunks[0]
    buffer_emb = embeddings[0]

    for i in range(1, len(chunks)):
        sim = cosine_similarity(buffer_emb, embeddings[i])
        if sim > 0.85:
            buffer["text"] += " " + chunks[i]["text"]
            buffer_emb = embedding_model.embed_documents([buffer["text"]])[0]
        else:
            final_chunk.append(buffer)
            buffer = chunks[i]
            buffer_emb = embeddings[i]
    final_chunk.append(buffer)
    return final_chunk

# Table Chunking
def chunk_table_csv(csv_path: Path, source_pdf: str, rows_per_chunk: int = 10) -> List[Dict]:
    try:
        df = pd.read_csv(csv_path)
    except Exception:
        return []
        
    chunks = []
    headers = " | ".join(df.columns)
    for start in range(0, len(df), rows_per_chunk):
        window = df.iloc[start:start + rows_per_chunk]
        rows_text = []
        for _, row in window.iterrows():
            rows_text.append(" | ".join(map(str, row.values)))
        
        chunk_text = f"Table Columns:\n{headers}\n\nRows:\n" + "\n".join(rows_text)
        chunks.append({
            "chunk_id": f"{csv_path.stem}_rows_{len(chunks)}",
            "type": "table",
            "source": source_pdf,
            "content": chunk_text
        })
    return chunks

# Image Chunking
def chunk_images(image_dir: Path, source_pdf: str) -> List[Dict]:
    image_chunks = []
    supported_ext = {".png", ".jpg", ".jpeg", ".webp"}
    if not image_dir.exists():
        return []
    for idx, img_path in enumerate(sorted(image_dir.iterdir())):
        if img_path.suffix.lower() not in supported_ext:
            continue
        image_chunks.append({
            "chunk_id": f"{Path(source_pdf).stem}_img_{idx}",
            "type": "image",
            "modality": "image",
            "image_path": str(img_path),
            "source": source_pdf,
            "page": None,          
            "caption": None 
        })
    return image_chunks

# OCR Chunking
def clean_ocr_text(text: str) -> str:
    text = text.replace("\x0c", " ") 
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()

def chunk_ocr_text(ocr_dir: Path, source_pdf: str, chunk_size=800, chunk_overlap=100) -> List[Dict]:
    ocr_chunks = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    if not ocr_dir.exists():
        return []

    for ocr_file in sorted(ocr_dir.glob("*.txt")):
        raw_text = ocr_file.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_ocr_text(raw_text)
        if not cleaned: continue

        splits = splitter.split_text(cleaned)
        for idx, chunk in enumerate(splits):
            ocr_chunks.append({
                "chunk_id": f"{Path(source_pdf).stem}_ocr_{ocr_file.stem}_{idx}",
                "type": "text",
                "modality": "ocr",
                "content": chunk,
                "source": source_pdf,
                "page": None
            })
    return ocr_chunks

def main():
    print("--- Starting Chunking ---")
    source_pdf = "sample.pdf" # In a real looped pipeline this would be dynamic

    # 1. Text Chunks
    print("Chunking Docling JSON...")
    all_text_chunks = []
    for json_file in JSON_DIR.glob("*_docling.json"):
        doc_chunks = chunk_docling_json(json_file)
        for ch in doc_chunks:
            all_text_chunks.append({
                "chunk_id": f"{json_file.stem}_{len(all_text_chunks)}",
                "source": source_pdf,
                "page": ch["page"],
                "type": "text",
                "content": ch["text"]
            })
    with open(CHUNKS_DIR / "docling_text_chunks.json", "w") as f:
        json.dump(all_text_chunks, f, indent=2)
    print(f"Text chunks: {len(all_text_chunks)}")

    # 2. Table Chunks
    print("Chunking Tables...")
    all_table_chunks = []
    for csv_file in TABLE_DIR.glob("*.csv"):
        all_table_chunks.extend(chunk_table_csv(csv_file, source_pdf))
    with open(CHUNKS_DIR / "table_chunks.json", "w") as f:
        json.dump(all_table_chunks, f, indent=2)
    print(f"Table chunks: {len(all_table_chunks)}")

    # 3. Image Chunks
    print("Chunking Images...")
    all_image_chunks = chunk_images(IMAGE_DIR, source_pdf)
    with open(CHUNKS_DIR / "image_chunks.json", "w") as f:
        json.dump(all_image_chunks, f, indent=2)
    print(f"Image chunks: {len(all_image_chunks)}")

    # 4. OCR Chunks
    print("Chunking OCR...")
    all_ocr_chunks = chunk_ocr_text(OCR_DIR, source_pdf)
    with open(CHUNKS_DIR / "ocr_chunks.json", "w") as f:
        json.dump(all_ocr_chunks, f, indent=2)
    print(f"OCR chunks: {len(all_ocr_chunks)}")

if __name__ == "__main__":
    main()
