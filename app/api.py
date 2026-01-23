from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.rag import rag_answer
from app.retrieval import get_vector_stats

app = FastAPI(title="Multimodal RAG API")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    citations: list

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    try:
        response = rag_answer(request.query)
        return {
            "answer": response["answer"],
            "citations":response.get("citations",[])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "multimodal-rag-api"
    }

@app.get("/stats")
def stats():
    stats = get_vector_stats()
    return{
        "chunks_indexed": stats["vector_count"],
        "vectorstore": stats["collection_name"]
    }