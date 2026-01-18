import requests
from typing import Dict
from app.config import OPENROUTER_API_KEY, LLM_MODEL
from app.retrieval import retrieve_context, deduplicate_chunks, retrieve_images_for_query
from app.prompt import build_prompt

def call_llm(prompt: str) -> Dict:
    """
    Call the OpenRouter API.
    """
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set in configuration.")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    if response.status_code != 200:
        return {
            "text": f"Error: {response.text}",
            "raw_response": response.json() if response.content else {}
        }

    data = response.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        text = "Error parsing response."

    return {
        "text": text,
        "raw_response": data
    }

def rag_answer(query: str) -> Dict:
    """
    Main RAG pipeline entry point.
    """
    retrieved_docs = retrieve_context(query, k=6)
    retrieved_docs = deduplicate_chunks(retrieved_docs)

    prompt = build_prompt(query, retrieved_docs)
    llm_result = call_llm(prompt)

    return {
        "query": query,
        "answer": llm_result["text"],
        "citations": [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in retrieved_docs
        ],
        "images": retrieve_images_for_query(query)
    }
