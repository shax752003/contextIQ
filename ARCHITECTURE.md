## System Architecture

### Offline Pipeline
- PDF ingestion
- Extraction
- Chunking
- Embedding
- Vector indexing

Executed via:
python -m pipelines.run_all

### Online Serving
- FastAPI application
- RAG retrieval over persisted vector store
- Stateless Docker container

### Storage
- data/: raw + processed documents
- vectorstore/: embeddings and index
- Mounted into container at runtime

### Deployment Model
- Stateless API
- Stateful volumes
- Rebuild-safe and reproducible
