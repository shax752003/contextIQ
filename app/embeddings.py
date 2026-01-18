from langchain_huggingface import HuggingFaceEmbeddings
from app.config import EMBEDDING_MODEL_NAME

def get_embedding_model() -> HuggingFaceEmbeddings:
    """
    Initialize and return the HuggingFace embedding model.
    """
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME
    )
