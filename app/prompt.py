from typing import List

def build_prompt(query: str, docs: List) -> str:
    """
    Construct the final prompt for the LLM using retrieved documents.
    """
    context_text = ""

    for i, doc in enumerate(docs):
        meta = doc.metadata or {}
        context_text += (
            f"\n[Context {i+1} | page {meta.get('page','?')}]\n"
            f"{doc.page_content}\n"
        )

    instruction = (
        "Answer ONLY using the given context.\n"
        "If the answer is not present in the context, say:\n"
        "'Not specified in the provided document.'\n"
        "Do NOT guess or add outside knowledge."
    )
    return f"""
You are a technical assistant.

{instruction}

Context:
{context_text}

Question:
{query}

Answer:
"""
