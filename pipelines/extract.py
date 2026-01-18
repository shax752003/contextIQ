import os
import json
import uuid
import magic
import fitz  # PyMuPDF
import cv2
import numpy as np
import pytesseract
import camelot
from pathlib import Path
from typing import List, Dict, Any, Tuple
from docling.document_converter import DocumentConverter
from pdf2image import convert_from_path
from PIL import Image
from app.config import DATA_DIR
from app.utils import save_json, is_pdf, extract_pdf_metadata

RAW_DIR = DATA_DIR / "raw"
EXTRACTED_DIR = DATA_DIR / "extracted"

for sub in ["json", "tables", "images", "ocr", "metadata"]:
    (EXTRACTED_DIR / sub).mkdir(parents=True, exist_ok=True)

def save_metadata(metadata: Dict):
    pdf_name = metadata.get("file_name", "unknown")
    output_folder = EXTRACTED_DIR / "metadata" / f"{pdf_name}_metadata.json"
    save_json(metadata, output_folder)
    return output_folder


def extract_text_docling(pdf_path: Path) -> dict:
    result = {
        "docling_json": None,
        "page_texts": [],
        "extractor": None
    }
    try:
        converter = DocumentConverter()
        res = converter.convert(str(pdf_path))
        doc = res.document

        json_path = EXTRACTED_DIR / "json" / f"{pdf_path.stem}_docling.json"
        save_json(doc.export_to_dict(), json_path)
        result["docling_json"] = str(json_path)

        try:
            doc_fitz = fitz.open(str(pdf_path))
            for page in doc_fitz:
                result["page_texts"].append(page.get_text("text"))
            doc_fitz.close()
        except:
            full_text = (
                doc.export_to_text()
                if hasattr(doc, "export_to_text")
                else doc.export_to_markdown()
            )
            result["page_texts"] = [full_text]

        result["extractor"] = "docling + pymupdf"
        return result

    except:
        try:
            result["extractor"] = "pymupdf"
            doc_fitz = fitz.open(str(pdf_path))
            for page in doc_fitz:
                result["page_texts"].append(page.get_text("text"))
            doc_fitz.close()

        except Exception as e2:
            result["page_texts"] = []
            result["error"] = str(e2)

        return result

def extract_tables(pdf_path: Path) -> List[Dict[str, Any]]:
    tables = []
    try:
        tables_lattice = camelot.read_pdf(
            str(pdf_path),
            pages="all",
            flavor="lattice",
            edge_tol=50
        )
    except Exception:
        tables_lattice = []

    # save lattice tables
    if tables_lattice:
        for i, t in enumerate(tables_lattice):
            csv_path = EXTRACTED_DIR / "tables" / f"{pdf_path.stem}_lattice_{i}.csv"
            t.to_csv(str(csv_path), index=False)
            tables.append({
                "csv_path": str(csv_path),
                "pages": None,
                "extractor": "lattice"
            })
    try:
        tables_stream = camelot.read_pdf(
            str(pdf_path),
            pages="all",
            flavor="stream"
        )
    except Exception:
        tables_stream = []

    # save stream tables
    if tables_stream:
        for i, t in enumerate(tables_stream):
            csv_path = EXTRACTED_DIR / "tables" / f"{pdf_path.stem}_stream_{i}.csv"
            t.to_csv(str(csv_path), index=False)
            tables.append({
                "csv_path": str(csv_path),
                "pages": None,
                "extractor": "stream"
            })

    return tables

def extract_images_with_bbox(pdf_path: Path) -> List[Dict[str, Any]]:
    output = []

    # PyMuPDF extraction (embedded images)
    doc = fitz.open(str(pdf_path))
    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        images = page.get_images(full=True)

        for img_idx, img in enumerate(images):
            xref = img[0]
            try:
                base = doc.extract_image(xref)
            except Exception:
                continue
            img_bytes = base["image"]
            ext = base.get("ext", "png")

            img_name = f"{pdf_path.stem}_p{page_index+1}_embed_{img_idx}.{ext}"
            img_path = EXTRACTED_DIR / "images" / img_name
            with open(img_path, "wb") as f:
                f.write(img_bytes)

            bbox = None
            try:
                for inst in page.get_images(full=True):
                    if inst[0] == xref and len(inst) >= 9:
                        rect = None
                        if len(inst) > 7:
                            value = inst[7]
                            if isinstance(value, fitz.Rect):
                                rect = value
                        if rect:
                            bbox = [rect.x0, rect.y0, rect.x1, rect.y1]
                        break
            except:
                bbox = None

            output.append(
                {
                    "img_path": str(img_path),
                    "page": page_index + 1,
                    "bbox": bbox,
                    "width": base.get("width"),
                    "height": base.get("height"),
                    "extractor": "pymupdf"
                }
            )
    doc.close()

    # pdf2image extraction (page render images)
    try:
        pages = convert_from_path(str(pdf_path), dpi=200)
        for i, pil_img in enumerate(pages):
            img_name = f"{pdf_path.stem}_p{i+1}_render.png"
            img_path = EXTRACTED_DIR / "images" / img_name
            pil_img.save(img_path, "PNG")

            output.append(
                {
                    "img_path": str(img_path),
                    "page": i + 1,
                    "bbox": None,
                    "width": pil_img.width,
                    "height": pil_img.height,
                    "extractor": "pdf2image"
                }
            )
    except Exception as e:
        print(f"pdf2image failed: {e}")
    
    return output

def extract_ocr(image_dir: Path = None):
    if image_dir is None:
        image_dir = EXTRACTED_DIR / "images"
        
    all_images = list(image_dir.glob("*.png")) + list(image_dir.glob("*.jpeg"))
    ocr_path = EXTRACTED_DIR / "ocr"
    ocr_path.mkdir(parents=True, exist_ok=True)

    for i, image in enumerate(all_images):
        print(f"OCR processing {image.name}...")
        try:
            text = pytesseract.image_to_string(str(image))
            file_name = f"ocr_{image.stem}.txt"
            file_path = ocr_path / file_name
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"OCR failed for {image}: {e}")

def process_pdf(pdf_path: Path):
    pipeline_status: Dict[str, Any] = {"file_name": pdf_path.name}

    # Check if already extracted
    docling_path = EXTRACTED_DIR / "json" / f"{pdf_path.stem}_docling.json"
    if docling_path.exists():
        print(f"Skipping {pdf_path.name} (already extracted)")
        pipeline_status["status"] = "skipped"
        return pipeline_status

    try:
        print("attempting metadata extraction...")
        metadata = extract_pdf_metadata(pdf_path)
        save_metadata(metadata)
        pipeline_status["metadata_status"] = "success"
    except Exception as e:
        print(f"error in attempting metadata extraction {e}")
        pipeline_status["metadata_status"] = f"failed:{str(e)}"

    try:
        print("attempting text extraction...")
        extract_text_docling(pdf_path)
        pipeline_status["text_status"] = "success"
    except Exception as e:
        print(f"error in attempting text extraction {e}")
        pipeline_status["text_status"] = f"failed:{str(e)}"

    try:
        print("attempting image extraction...")
        extract_images_with_bbox(pdf_path)
        pipeline_status["image_status"] = "success"
    except Exception as e:
        print(f"error in attempting image extraction {e}")
        pipeline_status["image_status"] = f"failed:{str(e)}"

    try:
        print("attempting table extraction...")
        extract_tables(pdf_path)
        pipeline_status["table_status"] = "success"
    except Exception as e:
        print(f"error in attempting table extraction {e}")
        pipeline_status["table_status"] = f"failed:{str(e)}"

    try:
        print("attempting ocr extraction...")
        extract_ocr(EXTRACTED_DIR / "images")
        pipeline_status["ocr_status"] = "success"
    except Exception as e:
        print(f"error in attempting ocr extraction {e}")
        pipeline_status["ocr_status"] = f"failed:{str(e)}"

    return pipeline_status

def main():
    print("--- Starting Extraction ---")
    pdf_files = list(RAW_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {RAW_DIR}")
        return

    for pdf in pdf_files:
        print(f"Processing {pdf.name}...")
        status = process_pdf(pdf)
        print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
