
import sys

import chromadb

from src.infrastructure.chroma.collection import create_phase6_collections
from src.infrastructure.chroma.scoped import query_records, write_records

persist_path = sys.argv[1]
mode = sys.argv[2]

client = chromadb.PersistentClient(path=persist_path)
documents, _ = create_phase6_collections(client)

if mode == "write":
    write_records(
        collection=documents,
        startup_id="restart-test-startup",
        ids=["restart-test-record"],
        vectors=[[1.0, 0.0, 0.0]],
        texts=["persisted across a process restart"],
        metadatas=[
            {
                "document_id": "restart-test-document",
                "filename": "restart.txt",
                "page_number": 1,
                "chunk_index": 0,
                "is_active": True,
                "record_type": "document_chunk",
            }
        ],
    )
    print("WRITE_OK")

elif mode == "read":
    result = query_records(
        collection=documents,
        startup_id="restart-test-startup",
        query_vector=[1.0, 0.0, 0.0],
        result_count=5,
    )
    assert result["ids"][0] == ["restart-test-record"], result["ids"]
    print("READ_OK")

else:
    raise ValueError(f"Unsupported mode: {mode}")
