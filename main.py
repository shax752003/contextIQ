from app.rag import rag_answer

def main():
    query = "What problem does the AutoFactory dataset aim to solve in industrial automation, and why were existing datasets insufficient?"
    print(f"Query: {query}\n")
    
    try:
        response = rag_answer(query)
        print("Answer:")
        print(response["answer"])
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("Please ensure OPENROUTER_API_KEY is set in your .env file or environment variables.")
    except Exception as e:
        print(f"Error during RAG execution: {e}")

if __name__ == "__main__":
    main()
