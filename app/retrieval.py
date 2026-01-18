import numpy as np
from typing import List, Dict, Optional
from langchain_community.vectorstores import Chroma
from app.config import CHROMA_DIR
from app.embeddings import get_embedding_model

def get_vectorstore():
    """
    Initialize and return the Chroma vectorstore.
    """
    embedding_model = get_embedding_model()
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embedding_model
    )

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def expand_query(query: str) -> List[str]:
    """
    Expand the user query into multiple variations for better recall.
    """
    return [
        query,
        f"defination of {query}",
        f"{query} explained",
        f"{query} in the document"
    ]

def deduplicate_chunks(docs, threshold: float = 0.92):
    """
    Deduplicate retrieved chunks based on embedding similarity.
    """
    unique_docs = []
    stored_embeddings = []
    embedding_model = get_embedding_model()

    for doc in docs:
        # Note: This is expensive if we re-embed every time. 
        # Ideally, we should fetch embeddings from the vectorstore if possible, 
        # or cache them. For now, following notebook logic.
        emb = embedding_model.embed_documents([doc.page_content])[0]
        is_duplicate = False
        for stored_emb in stored_embeddings:
            if cosine_similarity(emb, stored_emb) > threshold:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_docs.append(doc)
            stored_embeddings.append(emb)
        
    return unique_docs

def retrieve_context(query: str, k: int = 6) -> List:
    """
    Retrieve relevant documents for a given query.
    """
    vectorstore = get_vectorstore()
    expanded_queries = expand_query(query)

    all_docs = []

    for q in expanded_queries:
        results = vectorstore.similarity_search(q, k=k)
        for doc in results:
            all_docs.append(doc)
    
    return all_docs

def retrieve_images_for_query(query: str):
    """
    Placeholder for image retrieval.
    """
    # placeholder for future CLIP / vision ranking
    return []
