from pipelines import ingest, extract, chunk, embed

def main():
    print("========================================")
    print("      RUNNING END-TO-END PIPELINE       ")
    print("========================================")
    
    print("\n[STEP 1] Data Ingestion")
    ingest.main()
    
    print("\n[STEP 2] Data Extraction")
    extract.main()
    
    print("\n[STEP 3] Chunking")
    chunk.main()
    
    print("\n[STEP 4] Embedding & Indexing")
    embed.build_vector_index()
    
    print("\n========================================")
    print("      PIPELINE COMPLETED SUCCESSFULLY     ")
    print("========================================")

if __name__ == "__main__":
    main()
