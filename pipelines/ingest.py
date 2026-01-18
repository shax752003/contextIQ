import os
import magic
import fitz
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from app.config import DATA_DIR

RAW_DATA_DIR = DATA_DIR / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

def is_pdf(file_path):
    try:
        file_type = magic.from_file(str(file_path), mime=True)
        print(f"Detected MIME for {file_path}: {file_type}")
        return file_type == "application/pdf"
    except Exception as e:
        print(f"Error checking mime type for {file_path}: {e}")
        return False

def extract_pdf_metadata(pdf_path):
    pdf_path = Path(pdf_path)
    try:
        doc = fitz.open(pdf_path)
        meta = doc.metadata
        info = {
            "file_name": pdf_path.name,
            "path": str(pdf_path),
            "pages": len(doc),
            "title": meta.get("title", None),
            "author": meta.get("author", None),
            "filesize_kb": round(os.path.getsize(pdf_path) / 1024, 2),
        }
        doc.close()
        return info
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def main():
    print("--- Starting Ingestion ---")
    pdf_files = list(RAW_DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {RAW_DATA_DIR}")
        return

    metadata_list = []
    print(f"Found {len(pdf_files)} PDFs. Extracting metadata...")

    for pdf in tqdm(pdf_files):
        if is_pdf(pdf):
            meta = extract_pdf_metadata(pdf)
            if meta:
                metadata_list.append(meta)
        else:
            print(f"Skipping non-PDF file: {pdf}")

    if metadata_list:
        df_metadata = pd.DataFrame(metadata_list)
        output_path = RAW_DATA_DIR / "metadata.csv"
        df_metadata.to_csv(output_path, index=False)
        print(f"Saved metadata to {output_path}")
        print(df_metadata)
    else:
        print("No valid metadata extracted.")

if __name__ == "__main__":
    main()
