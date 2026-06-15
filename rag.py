# ============================================================
#  rag.py — Retrieval Augmented Generation Pipeline for BizRadar AI
# ============================================================
#
#  What this file does:
#  Implements the complete two-phase RAG pipeline for BizRadar AI.
#  Phase 1 — Ingestion (runs once per document):
#      PDF → paragraph chunks → Gemini embeddings → ChromaDB persistent store
#  Phase 2 — Retrieval (runs on every user query):
#      User question → Gemini embedding → cosine similarity search → top 3 chunks
#
#  What this file does NOT handle:
#  Does not manage conversation history — that belongs to context_manager.py.
#  Does not call the LLM for answer generation — that belongs to agent.py.
#  Does not define the search_documents tool wrapper — that belongs to tools.py.
#
#  Functions:
#  - ingest_pdf()      → PDF file path → flat list of paragraph chunk dicts
#  - embed_and_store() → chunk list → vectors stored in ChromaDB, returns status string
#  - query_rag()       → user question string → top 3 relevant chunks with metadata
#
#  Used by:
#  - app.py   → calls ingest_pdf() + embed_and_store() at startup if user uploads a PDF
#  - tools.py → calls query_rag() inside search_documents() tool function
#
#  Design Decisions:
#  - PersistentClient: data survives between sessions — Client() would lose data on exit
#  - gemini-embedding-001: stable production embedding model available on free tier API keys.
#                          Same model used for both ingestion and querying — vector space consistency.
#                          text-embedding-004 was unavailable on this API key version (404 NOT_FOUND).
#  - MD5 hash as chunk ID: prevents duplicate ingestion even if the same PDF is renamed
#  - \n\n paragraph splitting: each paragraph contains one complete idea — meaningful retrieval unit
#  - Metadata stored per chunk: enables page-level citations and future filename filtering
#  - n_results=3: reduced from 5 — prevents Stage 4 RAG results from bloating self.messages
#                 context and crowding out Stage 2/3 reasoning room in the agent loop
#  - heartbeat() check: verifies ChromaDB connection before attempting ingestion
# ============================================================

import os
import hashlib

import chromadb
import pdfplumber
from google import genai
from dotenv import load_dotenv


# ── ENVIRONMENT & CLIENT SETUP ────────────────────────────────
# Runs once at module load — clients reused across all function calls.
# load_dotenv() must run before os.getenv() to populate the environment.

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Embedding model used for both ingestion and retrieval.
# Must stay identical across both phases — changing this after ingestion
# requires deleting database/chroma_db/ and re-ingesting all documents.
# gemini-embedding-001 chosen over text-embedding-004 — 404 on this API key version.
EMBEDDING_MODEL = "gemini-embedding-001"

# PersistentClient writes to disk — data survives between sessions.
# get_or_create_collection: safe to call on every restart, no crash if collection exists.
client     = chromadb.PersistentClient(path="./database/chroma_db")
collection = client.get_or_create_collection(name="data_storage")


# ── PHASE 1a — PDF INGESTION ──────────────────────────────────

def ingest_pdf(file_path: str) -> list:
    """Extract and chunk text from a PDF file for RAG ingestion.

    Opens the PDF page by page, extracts plain text, splits into paragraph-level
    chunks via double newline, and returns a flat list of chunk dicts with metadata.

    Parameters:
        file_path (str) → absolute or relative path to the PDF file

    Returns:
        list → flat list of dicts, each with keys:
               - "text"        (str)  → paragraph content
               - "page_number" (int)  → 1-indexed page the paragraph came from
               - "file_name"   (str)  → basename of the source file (no directory path)

    Why paragraph chunking:
        Each paragraph typically contains one complete idea — meaningful retrieval unit.
        Too-large chunks dilute relevance; too-small chunks lose context. Paragraphs balance both.

    Why pdfplumber over PyPDF2:
        pdfplumber handles complex PDF layouts (tables, columns, multi-font pitch decks)
        more reliably than PyPDF2, which can scramble reading order on non-linear layouts.
    """

    file_name = os.path.basename(file_path)  # strip directory path — store filename only
    chunks    = []

    with pdfplumber.open(file_path) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            text = page.extract_text()

            if not text:
                continue  # skip pages with no extractable text (images, blank pages)

            # Split on double newline — standard paragraph separator in extracted PDF text.
            # Strip whitespace and filter empty strings in one list comprehension.
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            for para in paragraphs:
                chunks.append({
                    "text":        para,
                    "page_number": page_number,
                    "file_name":   file_name
                })

    return chunks


# ── PHASE 1b — EMBED & STORE ──────────────────────────────────

def embed_and_store(new_chunks: list) -> str:
    """Convert paragraph chunks to vectors and store in ChromaDB.

    Sends all chunk texts to Gemini in a single batch API call, pairs each
    embedding with its source chunk via zip(), and writes all data to ChromaDB.
    Handles duplicate ingestion gracefully — same document can be re-submitted
    without crashing.

    Parameters:
        new_chunks (list) → flat list of chunk dicts from ingest_pdf()
                            each dict must have keys: "text", "page_number", "file_name"

    Returns:
        str → human-readable status message (success or duplicate or error notice)

    Why heartbeat() before ingestion:
        Verifies ChromaDB connection is live before attempting to write data.
        Catches database connectivity issues early with a clear error message
        rather than a cryptic failure mid-ingestion.

    Why single batch embed_content() call:
        One API call for all chunks is faster and cheaper than one call per chunk.
        Gemini's embed_content() accepts a list — no need to loop.

    Why gemini-embedding-001:
        text-embedding-004 returned 404 NOT_FOUND on this API key — unavailable
        on the v1beta API version used by google-genai SDK v1.75.0.
        gemini-embedding-001 is the stable production alternative available on free tier.

    Why MD5 hash as chunk ID:
        Deterministic — same text always produces the same ID.
        Prevents duplicate entries even when the same PDF is renamed before re-upload.
        ChromaDB raises DuplicateIDError if any ID already exists — caught below.

    Why zip(new_chunks, response.embeddings):
        Gemini returns embeddings in the same order as the input texts.
        zip() maintains this order alignment between source chunks and their vectors.
    """

    # Verify ChromaDB connection before attempting any write operations.
    # Returns a clear error string instead of crashing mid-ingestion.
    try:
        client.heartbeat()
    except Exception as e:
        return f"Connection to the database failed: {e}"

    # Extract all texts in one pass — passed as batch to Gemini embed_content()
    texts = [item["text"] for item in new_chunks]

    # Single Gemini API call for all chunk embeddings
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts
    )

    # Build parallel lists — ChromaDB add() requires each as a separate list
    ids        = []
    embeddings = []
    documents  = []
    metadatas  = []

    for chunk, embedding in zip(new_chunks, response.embeddings):

        # MD5 of chunk text — deterministic unique ID, prevents duplicate storage
        ids.append(hashlib.md5(chunk["text"].encode()).hexdigest())

        # embedding.values is the raw float list — ChromaDB stores this as the vector
        embeddings.append(embedding.values)

        documents.append(chunk["text"])

        # Metadata stored per chunk — enables page-level citations and filename filtering
        metadatas.append({
            "page_number": chunk["page_number"],
            "file_name":   chunk["file_name"]
        })

    try:
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        return "Data ingestion complete. Document saved successfully."

    except chromadb.errors.DuplicateIDError:
        # Raised when any chunk ID already exists in the collection.
        # Entire batch is rejected — graceful message returned instead of crash.
        return "This document has already been ingested. You can start querying it directly."


# ── PHASE 2 — RETRIEVAL ───────────────────────────────────────

def query_rag(user_input: str) -> list:
    """Convert a user question to a vector and retrieve the top 3 relevant chunks.

    Embeds the user question using the same model used during ingestion (vector space
    consistency), queries ChromaDB via cosine similarity, and returns matched chunks
    with their source metadata for citation.

    Parameters:
        user_input (str) → raw user question or search query

    Returns:
        list → list of dicts, each with keys:
               - "text"     (str)  → matched paragraph content
               - "metadata" (dict) → {"page_number": int, "file_name": str}

    Why same embedding model as embed_and_store():
        Vector space consistency — different models produce different dimensional spaces.
        Comparing vectors from different models produces meaningless similarity scores.
        Both phases use EMBEDDING_MODEL constant — single source of truth.
        Changing the model requires deleting database/chroma_db/ and re-ingesting.

    Why [response.embeddings[0].values]:
        ChromaDB expects query_embeddings as a list of float lists — one per query.
        response.embeddings returns a list of ContentEmbedding objects, not raw floats.
        .values extracts the float list. Wrapped in [] for single-query format ChromaDB expects.

    Why n_results=3 (reduced from 5):
        search_documents() is called as Stage 4, after Stages 1-3 have already populated
        self.messages with substantial context. Top-5 chunks bloated the message history
        and crowded out the LLM's reasoning room for final answer generation.
        Top-3 preserves enough context for citation and answer quality.
        Phase 4 will add dynamic k selection based on query complexity.

    Why zip(documents, metadatas):
        ChromaDB returns documents and metadatas as separate parallel lists under [0].
        zip() pairs each chunk with its metadata — enables source citations in agent responses.
    """

    # Embed user question — must use same model as ingestion for valid cosine comparison
    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[user_input]
    )

    # ChromaDB cosine similarity search — returns nested lists, [0] for single query.
    # response.embeddings[0].values extracts raw float list from ContentEmbedding object.
    # Wrapped in [] — ChromaDB expects list of embeddings, one per query.
    results = collection.query(
        query_embeddings=[response.embeddings[0].values],
        n_results=3
    )

    # Pair each chunk text with its metadata — enables page-level source citations
    return [
        {"text": text, "metadata": metadata}
        for text, metadata in zip(results["documents"][0], results["metadatas"][0])
    ]