import os 
import hashlib

import chromadb

from src.config.settings import (
    DEFAULT_VECTOR_TOP_K,
    CHROMA_DB_PATH,
    
    
)

def add_documents( chunks:list, embeddings:list):    # called ONCE at ingestion time
    client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH
    )
    
    collection = client.get_or_create_collection(
        name="data_storage"
    )
    
    ids_list        = []
    embeddings_list = []
    documents_list  = []
    metadatas_list  = []

    for chunk, embedding in zip(chunks, embeddings):

        # MD5 of chunk text — deterministic unique ID, prevents duplicate storage
        ids_list.append(hashlib.md5(chunk["text"].encode()).hexdigest())

        # embedding.values is the raw float list — ChromaDB stores this as the vector
        embeddings_list.append(embedding)

        documents_list.append(chunk["text"])

        # Metadata stored per chunk — enables page-level citations and
        # Phase 4's where={"file_name": ...} multi-document filtering
        metadatas_list.append({
            "page_number": chunk["page_number"],
            "file_name":   chunk["file_name"]
        })

    
    collection.add(
        ids=ids_list,
        embeddings=embeddings_list,
        documents=documents_list,
        metadatas=metadatas_list
    )

    return "Data ingestion complete. Document saved successfully."
    
def query_collection(user_input:list ,where:dict, top_k = DEFAULT_VECTOR_TOP_K):  # called at search time
    client = chromadb.PersistentClient(
        path=CHROMA_DB_PATH
    )
    
    collection = client.get_or_create_collection(
        name="data_storage"
    )
    
    results = collection.query(
        query_embeddings=user_input,
        where=where,
        n_results=top_k,
        include=[
            "documents",
            "metadatas",
            "distances"
        ],
    )
    
    if results["documents"][0]:
        return results 
    else:
        return []


if __name__ == "__main__":
    # 1. Mock Chunks (Input Data)
    mock_chunks = [
        {
            "text": "The Quick Start guide covers basic authentication steps using API keys.",
            "page_number": 1,
            "file_name": "api_documentation.pdf"
        },
        {
            "text": "Rate limits are enforced at 60 requests per minute per IP address.",
            "page_number": 4,
            "file_name": "api_documentation.pdf"
        },
        {
            "text": "Vector databases index high-dimensional embeddings for fast similarity search.",
            "page_number": 12,
            "file_name": "architecture_overview.pdf"
        }
    ]

    # 2. Mock Embeddings (Matching vectors)
    mock_embeddings = [
        [0.12, -0.43, 0.89, 0.05],  # Vector for Chunk 1
        [-0.71, 0.22, 0.15, -0.38], # Vector for Chunk 2
        [0.55, 0.61, -0.02, 0.74]   # Vector for Chunk 3
    ]

    for chunk, embeddings in zip(mock_chunks, mock_embeddings):
        print(add_documents(chunk= [chunk], embeddings= [embeddings]))
        print(query_collection(embeddings=[embeddings]))