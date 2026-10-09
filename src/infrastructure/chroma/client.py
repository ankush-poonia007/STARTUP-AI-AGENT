from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

def create_chroma_client(persist_dir:str | Path ) -> chromadb.PersistentClient :
    """Create and return a ChromaDB client."""
    
    path = Path(persist_dir)
    
    path.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(path),
        settings=ChromaSettings(
            anonymized_telemetry=False,
        ),
    )
    
    return client


if __name__ == "__main__":
    
    import subprocess
    import sys
    import tempfile

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:           
        # Process 1: write a test vector.
        # Process 1: write a test vector.
        client = create_chroma_client(temp_dir)
        collection = client.get_or_create_collection(
            name="persistence_test"
        )
        collection.upsert(
            ids=["test-vector-1"],
            embeddings=[[0.1, 0.2, 0.3]],
            documents=["Chroma persistence verification"],
        )

        print("Process 1: Test vector written.")

        # Release references before starting the next process.
        del collection
        del client

        # Process 2: reopen storage and verify persistence.
        verification_script = """
import sys
from src.infrastructure.chroma.client import create_chroma_client

client = create_chroma_client(sys.argv[1])
collection = client.get_collection(name="persistence_test")
result = collection.get(ids=["test-vector-1"], include=["documents"])

assert result["ids"] == ["test-vector-1"], "Persisted vector ID not found."
assert result["documents"] == ["Chroma persistence verification"], "Persisted document mismatch."

print("Process 2: Persistence verified successfully.")
"""

        subprocess.run(
            [sys.executable, "-c", verification_script, temp_dir],
            check=True,
        )

        print("PASS: Data persisted across separate Python processes.")