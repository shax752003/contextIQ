import pandas as pd
from pathlib import Path
from tqdm import tqdm
from app.config import DATA_DIR
from app.utils import is_pdf, extract_pdf_metadata

RAW_DATA_DIR = DATA_DIR / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

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
