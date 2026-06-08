# ChromaDB collection setup
import chromadb
import pdfplumber
import os
from google import genai 
import hashlib 

# Step 1 : Create ChromaDB client and collection. 
client = chromadb.PersistentClient(path="./database/chroma_db")
gemini_client = genai.Client()

collection = client.get_or_create_collection(name = "data_storage")


# ingest_pdf() — chunk, embed via Gemini, store with metadata
# Receive path as input
def ingest_pdf(file_path:str) -> list:

    # Get filename using os.path.basename(path)
    file_name = os.path.basename(file_path)
    chunks = []
    
    # Open PDF using pdfplumber
    with pdfplumber.open(file_path) as pdf:
        
        # Loop through pages using enumerate starting at 1
        for page_number, page in enumerate(pdf.pages,start = 1 ):
            
            # Extract text — skip if None
            text = page.extract_text()
            if text :
                
                # Split by \n\n — filter empty chunks
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                
                # For each valid chunk create dict with keys text, page_number, filename
                for para in paragraphs:
                    
                    # Append to chunks list
                    chunks.append(
                        {
                            "text":para,
                            "page_number":page_number,
                            "file_name":file_name
                        }
                    )
                    
    # Return chunks          
    return chunks

# query_rag() — embed question via Gemini, cosine search, return chunks
# Input — flat chunks list
def embed_and_store(new_chunks:list):
    
  
    # Step 1 : Collect all the texts in one list called texts
    texts = [item["text"] for item in new_chunks]
  
    # Step 2 : Call Gemini API embed_content() with texts - get back result
    response = gemini_client.models.embed_content(
        model="text-embedding-004",
        contents=texts
    )
    
    # Step 3 : Create empty lists to store the data in order
    ids = []
    embeddings = []
    documents = []
    metadatas = []
    
    # Step 4 : Iterate over the resposne.embeddings using zip to make sure that we are in correct order 
    for chunk, embedding in zip(new_chunks, response.embeddings):
        
        # Update ids using chunk["text"] anc create the new hashlib id 
        ids.append(hashlib.md5(chunk["text"].encode()).hexdigest())
        
        # Update the embeddings values from embedding
        embeddings.append(embedding.values)
        
        # Update the document with chuks["texts"]
        documents.append(chunk["text"])
        
        # Update the meta data with filtering dict key values 
        metadatas.append(
            {
            "page_number": chunk["page_number"],
            "file_name": chunk["file_name"]
            }
        )
    
    # Step 5: Udating the database using .add( with parameters ) to store this data into chromadatabase
    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        
        return "Data ingestion complete. Data saved successfully."

    except chromadb.errors.DuplicateIDError:
        return "This document has already been ingested. You can start querying it directly."    

def query_rag(user_input:str):
    
    # Step 1 : Convert the user_input into vectors 
    response = gemini_client.models.embed_content(
        model="text-embedding-004",
        contents=[user_input]
    )
    
    # Step 2 : Search the Vectors using cosine similarity
    results = collection.query(
        query_embeddings = response.embeddings,
        n_results = 5
    )
    
    return results["documents"][0]