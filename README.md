📄 ContextIQ: Multimodal RAG System

Text • Tables • OCR • Citation-Grounded Answers

🔍 Overview

ContextIQ is a production-grade multimodal Retrieval-Augmented Generation (RAG) pipeline designed to handle complex PDFs containing tables, scanned text, and images. It accurately retrieves and answers questions by processing various modalities separately and preserving their context, preventing hallucinations common in standard RAG systems.

The system uses advanced extraction techniques to handle real-world documents and provides reliable, citation-grounded responses.

🎯 Problem Statement

Most basic RAG pipelines:

- Flatten tables into unreadable text
- Lose context across pages
- Hallucinate answers when definitions are missing
- Fail on scanned or OCR-heavy documents

ContextIQ solves these issues by building a structured, modality-aware RAG pipeline that treats tables and OCR content as first-class citizens.

🧠 Solution Highlights

- **Multimodal extraction**: Extracts text, tables (using Camelot), images, and OCR content (using Tesseract/Docling).
- **Specialized Chunking**: Separate handling for text, tables, and images to preserve structure.
- **Citation-grounded generation**: Answers are strictly based on retrieved context with page references.
- **Vector-based retrieval**: Uses ChromaDB with HuggingFace embeddings for precise semantic search.
- **Open Model Support**: Integrates with OpenRouter (using Gemma-3-27b or compatible models) for generation.

🏗️ Architecture
```mermaid
graph TD
    PDF[PDF Document] --> Extraction
    subgraph Extraction
        Docling[Docling/PyMuPDF] --> Text
        Camelot[Camelot] --> Tables
        OCR[Tesseract] --> ScannedText
        Images[PDF2Image] --> Visuals
    end
    Extraction --> Normalization[Cleaning & Normalization]
    Normalization --> Chunking[Modality-Aware Chunking]
    Chunking --> Embedding[HuggingFace Embeddings]
    Embedding --> VectorDB[(ChromaDB)]
    
    User[User Query] --> VectorDB
    VectorDB --> Retrieval[Top-K Retrieval]
    Retrieval --> LLM[LLM (OpenRouter/Gemma)]
    LLM --> Answer[Grounded Answer + Citations]
```

📁 Project Structure
```text
contextIQ/
│
├── notebook/
│   ├── 01_data_ingestion.ipynb       # Raw data handling
│   ├── 02_data_extraction.ipynb      # Docling, Camelot, OCR extraction
│   ├── 03_chunking.ipynb             # Text and table chunking strategies
│   ├── 04_embedding_vectorstore.ipynb # Embedding generation & ChromaDB indexing
│   └── 05_retrieval.ipynb            # RAG pipeline with OpenRouter
│
├── data/
│   ├── raw/          # Original PDFs
│   ├── extracted/    # Parsed text, tables, images, OCR
│   ├── chunks/       # JSON chunk files
│   └── chroma_db/    # Persisted vector database
│
├── src/              # Source code (modularized)
├── README.md         # Project documentation
├── requirements.txt  # Python dependencies
└── .gitignore
```

⚙️ Tech Stack

- **Language**: Python
- **LLM Framework**: LangChain
- **Vector Database**: ChromaDB
- **Embeddings**: HuggingFace Transformers (`all-MiniLM-L6-v2`)
- **LLM Provider**: OpenRouter (Gemma-3-27b / compatible models)
- **PDF Parsing**: Docling, PyMuPDF (Fitz), PDFPlumber
- **Table Extraction**: Camelot
- **OCR**: Pytesseract
- **Data Processing**: Pandas, NumPy

🔄 Pipeline Breakdown
1️⃣ PDF Extraction
- Extracts structured text using **Docling** and **PyMuPDF**.
- Extracts tabular data using **Camelot** (Lattice/Stream modes).
- Captures images and performs OCR on scanned pages using **Tesseract**.
- Preserves page-level metadata for accurate citations.

2️⃣ Cleaning & Normalization
- Removes OCR artifacts and noise.
- Normalizes whitespace and encoding.
- Separates tables from plain text to prevent structural loss.

3️⃣ Chunking Strategy
- **Text**: Recursive/semantic chunking for context preservation.
- **Tables**: Stored as atomic units to prevent splitting rows/columns.
- **OCR**: Processed as text chunks with metadata indicating origin.

4️⃣ Embedding & Indexing
- Converts chunks into dense vector embeddings using **HuggingFace (`all-MiniLM-L6-v2`)**.
- Stores vectors in **ChromaDB** for fast similarity search.
- Persists metadata including page numbers and modality type.

5️⃣ Retrieval & Generation
- Retrieves top-K relevant chunks using cosine similarity.
- **Multi-query expansion** to improve search recall.
- **Deduplication** to remove redundant chunks.
- Builds a context-only prompt to ensure answers are derived *only* from the documents.
- Generates answers via **OpenRouter** with strict strict prompt discipline.

🧪 Example Query

**Question:**
> Which five Named Entity Recognition (NER) categories are used in the AutoFactory dataset, and what do they represent?

**Answer (Generated):**
> The five NER categories in the AutoFactory dataset are: ACTUATOR, PRE-ACTUATOR, SENSOR, EFFECTOR, and OTHER. They represent requirement specifications for manufacturing systems (industrial automation).

**Source:** Page 19
