# BM25 Library 
import os
import bm25s
import json 
import hashlib
import os
import time

import chromadb
import pdfplumber

from dotenv import load_dotenv

from google import genai
from google.genai import types

from src.config.settings import (
    DEFAULT_VECTOR_TOP_K,
    DEFAULT_RERANK_TOP_K,
    GENERATION_MODEL,
    EMBEDDING_MODEL,
    BM25_INDEX_DIR,
    BM25_CORPUS_FILE,
)

from src.rag.reranker import rerank


# ============================================================
# Environment
# ============================================================

load_dotenv()

# ============================================================
# Gemini API Keys
# ============================================================

GEMINI_API_KEY_1 = os.getenv("GEMINI_API_KEY_1")
GEMINI_API_KEY_2 = os.getenv("GEMINI_API_KEY_2")
GEMINI_API_KEY_3 = os.getenv("GEMINI_API_KEY_3")
GEMINI_API_KEY_4 = os.getenv("GEMINI_API_KEY_4")
GEMINI_API_KEY_5 = os.getenv("GEMINI_API_KEY_5")
GEMINI_API_KEY_6 = os.getenv("GEMINI_API_KEY_6")
GEMINI_API_KEY_7 = os.getenv("GEMINI_API_KEY_7")
GEMINI_API_KEY_8 = os.getenv("GEMINI_API_KEY_8")
GEMINI_API_KEY_9 = os.getenv("GEMINI_API_KEY_9")
GEMINI_API_KEY_10 = os.getenv("GEMINI_API_KEY_10")
GEMINI_API_KEY_11 = os.getenv("GEMINI_API_KEY_11")
GEMINI_API_KEY_12 = os.getenv("GEMINI_API_KEY_12")
GEMINI_API_KEY_13 = os.getenv("GEMINI_API_KEY_13")
GEMINI_API_KEY_14 = os.getenv("GEMINI_API_KEY_14")
GEMINI_API_KEY_15 = os.getenv("GEMINI_API_KEY_15")
GEMINI_API_KEY_16 = os.getenv("GEMINI_API_KEY_16")
GEMINI_API_KEY_17 = os.getenv("GEMINI_API_KEY_17")
GEMINI_API_KEY_18 = os.getenv("GEMINI_API_KEY_18")
GEMINI_API_KEY_19 = os.getenv("GEMINI_API_KEY_19")
GEMINI_API_KEY_20 = os.getenv("GEMINI_API_KEY_20")

# ============================================================
# Gemini API Pool
# ============================================================

GEMINI_API_KEYS = [
    GEMINI_API_KEY_1,
    GEMINI_API_KEY_2,
    GEMINI_API_KEY_3,
    GEMINI_API_KEY_4,
    GEMINI_API_KEY_5,
    GEMINI_API_KEY_6,
    GEMINI_API_KEY_7,
    GEMINI_API_KEY_8,
    GEMINI_API_KEY_9,
    GEMINI_API_KEY_10,
    GEMINI_API_KEY_11,
    GEMINI_API_KEY_12,
    GEMINI_API_KEY_13,
    GEMINI_API_KEY_14,
    GEMINI_API_KEY_15,
    GEMINI_API_KEY_16,
    GEMINI_API_KEY_17,
    GEMINI_API_KEY_18,
    GEMINI_API_KEY_19,
    GEMINI_API_KEY_20,
]

GEMINI_API_KEYS = [
    key
    for key in GEMINI_API_KEYS
    if key
]

# ============================================================
# Dynamic API Pool Configuration
# ============================================================

API_COOLDOWN_SECONDS  = 60

_current_api_index = 0

api_pool = [
    {
        "client": genai.Client(api_key=key),
        "cooldown_until": 0.0,
        "requests": 0,
        "failures": 0,
    }
    for key in GEMINI_API_KEYS
]

# ============================================================
# Dedicated Embedding Client
# ============================================================

gemini_client_1 = genai.Client(
    api_key=GEMINI_API_KEY_1
)

# ============================================================
# Models
# ============================================================

# EMBEDDING_MODEL = "gemini-embedding-001"

# GENERATION_MODEL = "gemini-2.5-flash"

# ============================================================
# ChromaDB
# ============================================================

client = chromadb.PersistentClient(
    path="./data/chroma_db"
)

collection = client.get_or_create_collection(
    name="data_storage"
)


# Create folder if it doesn't exist
os.makedirs(BM25_INDEX_DIR, exist_ok=True)

# ============================================================
# Load Existing Corpus
# ============================================================

bm25_corpus = {}

try:
    with open(BM25_CORPUS_FILE, "r", encoding="utf-8") as file:
        print("🔄 Loading existing corpus...")
        bm25_corpus = json.load(file)

except FileNotFoundError:
    print("🆕 BM25 corpus not found.")
    
if not bm25_corpus:
    print("⚠️ ChromaDB is empty — skipping BM25 rebuild.")
else:
    
    print("🆕 BM25 corpus not found. Rebuilding from ChromaDB...")

    result = collection.get(
        include=["documents","metadatas"]
    )
    
    documents = result["documents"]
    metadatas = result["metadatas"]
    
    for documents, metadatas in zip(documents,metadatas):
        
        chunk = {
            "text":documents,
            **metadatas
        }
        
        bm25_corpus[documents] = chunk
    
    print("🔄 Rebuilding BM25 index...")
    full_corpus = list(bm25_corpus.keys())
    
    corpus_tokens = bm25s.tokenize(
        full_corpus,
        stopwords="english"
    )
    
    
    bm25_index = bm25s.BM25(corpus= full_corpus)
    bm25_index.index(corpus_tokens)
    
    bm25_index.save(
        BM25_INDEX_DIR,
        corpus=full_corpus
    )
    
    with open(BM25_CORPUS_FILE, 'w', encoding="utf-8") as file:
        json.dump(
            bm25_corpus,
            file,
            ensure_ascii=False,
            indent=4
        )
    
    print(f"✅ Restored {len(bm25_corpus)} chunks from ChromaDB.")
    
    
# ============================================================
# Load Existing BM25 Index
# ============================================================

try:
    bm25_index = bm25s.BM25.load(
        BM25_INDEX_DIR,
        load_corpus=True,
        mmap=False
    )
    print("🔄 Loaded existing BM25 index.")

except FileNotFoundError:
    print("🆕 No existing BM25 index found.")
    bm25_index = None
    
    
# ============================================================
# Gemini API Manager
# ============================================================


def get_next_available_client() -> tuple[int, genai.Client]:
    """
    Return the next available Gemini client.

    Strategy
    --------
    1. Start from the last successful API key.
    2. Skip keys currently in cooldown.
    3. Wrap around the pool if necessary.
    4. Raise an error if every key is unavailable.
    """

    global _current_api_index

    if not api_pool:
        raise RuntimeError(
            "No Gemini API keys have been configured."
        )

    current_time = time.time()
    total_keys = len(api_pool)

    for offset in range(total_keys):

        index = (_current_api_index + offset) % total_keys

        state = api_pool[index]

        if current_time >= state["cooldown_until"]:
            return index, state["client"]

    raise RuntimeError(
        "All Gemini API keys are currently in cooldown."
    )
    

# ============================================================
# API State Updates
# ============================================================

def mark_api_success(
    api_index: int,
) -> None:
    """
    Mark an API key as healthy after a successful request.

    Responsibilities
    ----------------
    1. Reset failure count.
    2. Remove cooldown.
    3. Remember this key as the preferred key.
    """

    global _current_api_index

    state = api_pool[api_index]

    # Reset failure tracking
    state["failures"] = 0

    # Clear cooldown immediately
    state["cooldown_until"] = 0.0

    # Continue future requests from this key
    _current_api_index = api_index
    

def mark_api_failed(
    api_index: int,
) -> None:
    """
    Mark an API key as temporarily unavailable.

    Strategy
    --------
    1. Increase failure count.
    2. Apply exponential cooldown.
    3. Advance to the next API key.
    """

    global _current_api_index

    state = api_pool[api_index]

    # Track consecutive failures
    state["failures"] += 1

    # Exponential backoff
    cooldown = min(
        300,  # Maximum cooldown (5 minutes)
        API_COOLDOWN_SECONDS
        * (2 ** (state["failures"] - 1))
    )

    state["cooldown_until"] = (
        time.time() + cooldown
    )

    # Move immediately to the next API key
    _current_api_index = (
        api_index + 1
    ) % len(api_pool)

    print(
        f"[Gemini] API Key {api_index + 1} "
        f"cooling down for {cooldown:.0f}s"
    )


# ============================================================
# API Pool Statistics
# ============================================================

def print_api_pool_status() -> None:
    """
    Print the runtime status of the Gemini API pool.

    Displays:
    - Current active API key
    - Total attempts
    - Consecutive failures
    - Remaining cooldown
    """

    if not api_pool:

        print("\nNo Gemini API keys configured.\n")

        return

    current_time = time.time()

    print()
    print("=" * 90)
    print("GEMINI API POOL STATUS")
    print("=" * 90)

    for index, state in enumerate(api_pool):

        remaining = max(
            0.0,
            state["cooldown_until"] - current_time,
        )

        status = (
            "ACTIVE"
            if remaining == 0
            else "COOLDOWN"
        )

        current_marker = (
            "  ← Current"
            if index == _current_api_index
            else ""
        )

        print(
            f"Key {index + 1:<2}"
            f"| Status: {status:<8}"
            f"| Attempts: {state['requests']:<5}"
            f"| Failures: {state['failures']:<3}"
            f"| Cooldown: {remaining:>6.1f}s"
            f"{current_marker}"
        )

    print("=" * 90)
    print()
    
    
# ============================================================
# Gemini Generation
# ============================================================

def gemini_generate_with_failover(
    prompt: str,
    *,
    model: str = GENERATION_MODEL,
    temperature: float = 0.0,
    max_retries: int = 2,
) -> str:
    """
    Generate text using Gemini with automatic API
    failover and intelligent retry logic.

    Features
    --------
    • Dynamic API rotation
    • Exponential cooldown
    • Automatic retry
    • Last successful API optimization
    • Runtime statistics
    """

    last_exception = None

    retries = 0

    while retries <= max_retries:

        attempted_keys = set()

        while len(attempted_keys) < len(api_pool):

            api_index, client = get_next_available_client()

            if api_index in attempted_keys:
                break

            attempted_keys.add(api_index)

            state = api_pool[api_index]

            # Count every request attempt
            state["requests"] += 1

            try:

                print(
                    f"[Gemini] "
                    f"Using API Key {api_index + 1}"
                )

                response = client.models.generate_content(

                    model=model,

                    contents=prompt,

                    config=types.GenerateContentConfig(

                        temperature=temperature,

                    ),

                )
                if not getattr(response, "text", None):
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )
                mark_api_success(api_index)

                return response.text

            except Exception as error:

                last_exception = error

                error_message = str(error).lower()

                # ----------------------------
                # Rate Limit / Quota Handling
                # ----------------------------

                if any(

                    keyword in error_message

                    for keyword in (

                        "429",
                        "quota",
                        "resource_exhausted",
                        "rate limit",

                    )

                ):

                    print(

                        f"[Gemini] "

                        f"API Key {api_index + 1} "

                        "rate limited."

                    )

                    mark_api_failed(api_index)

                    continue

                # ----------------------------
                # Temporary Server Errors
                # ----------------------------

                if any(

                    keyword in error_message

                    for keyword in (

                        "500",
                        "502",
                        "503",
                        "504",

                    )

                ):

                    print(

                        "[Gemini] "

                        "Temporary server error."

                    )

                    time.sleep(2)

                    continue

                # ----------------------------
                # Unknown Errors
                # ----------------------------

                raise

        retries += 1

        if retries <= max_retries:

            print(

                f"[Gemini] "

                f"Retry Attempt "

                f"{retries}/{max_retries}"

            )

            time.sleep(2)

    raise RuntimeError(

        f"Gemini generation failed after "

        f"{max_retries + 1} attempts."

    ) from last_exception
    
    
# ── PHASE 1a — PDF INGESTION ──────────────────────────────────

def ingest_pdf(file_path: str) -> list:
    

    file_name = os.path.basename(file_path)  # strip directory path — store filename only

    # ============================================================
    # Chunking Configuration
    # ============================================================

    CHUNK_SIZE = 250

    OVERLAP = 50

    STEP = CHUNK_SIZE - OVERLAP

    MIN_CHUNK_WORDS = 20
    
    chunks = []

    with pdfplumber.open(file_path) as pdf:

        for page_number, page in enumerate(pdf.pages, start=1):

            text = page.extract_text()

            if not text:
                continue  # skip pages with no extractable text (images, blank pages)

            # Split on double newline — standard paragraph separator in extracted PDF text.
            # Strip whitespace and filter empty strings in one list comprehension.
            paragraphs = [
                p.strip()
                for p in text.split("\n\n")
                if p.strip()
            ]

            chunk_index = 0

            for paragraph_text in paragraphs:

                words = paragraph_text.split()

                # Small paragraph → keep as-is, one complete idea per chunk
                if len(words) <= CHUNK_SIZE:

                    chunks.append({
                        "text": paragraph_text,
                        "page_number": page_number,
                        "file_name": file_name,
                        "chunk_index": chunk_index
                    })

                    chunk_index += 1

                # Large paragraph → sliding window chunking.
                # OVERLAP words repeat between consecutive windows so an idea
                # spanning the cut point isn't fully lost from either chunk.
                else:

                    left  = 0
                    right = CHUNK_SIZE

                    while left < len(words):

                        window_text = " ".join(words[left:right])

                        # Skip tiny trailing chunks
                        if len(window_text.split()) < MIN_CHUNK_WORDS:
                            break

                        chunks.append({
                            "text": window_text,
                            "page_number": page_number,
                            "file_name": file_name,
                            "chunk_index": chunk_index
                        })

                        chunk_index += 1
                        left  += STEP
                        right += STEP

    print(f"Length of Chunks: {len(chunks)}")

    # Guard against empty chunks list — max() on an empty generator raises
    # ValueError, which would crash ingestion for an all-image/scanned PDF
    # with no extractable text on any page, instead of returning [] cleanly.
    if chunks:
        max_chunk_len = max(len(c["text"].split()) for c in chunks)
        print(f"Maximum length of each chunk: {max_chunk_len}")
    else:
        print("Warning: no extractable text found in this PDF — 0 chunks produced.")

    return chunks


# ── PHASE 1b — EMBED & STORE ──────────────────────────────────

def embed_and_store(new_chunks: list) -> str:
    """Convert paragraph/window chunks to vectors and store in ChromaDB.

    Sends all chunk texts to Gemini in a single batch API call, pairs each
    embedding with its source chunk via zip(), and writes all data to ChromaDB.
    Handles duplicate ingestion gracefully — same document can be re-submitted
    without crashing.

    Parameters:
        new_chunks (list) → flat list of chunk dicts from ingest_pdf()
                            each dict must have keys: "text", "page_number", "file_name"

    Returns:
        str → human-readable status message (success, duplicate, or connection-error notice)

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

    Why metadata stores only page_number + file_name (not chunk_index):
        file_name is what Phase 4's where={"file_name": ...} filter scopes
        retrieval by, and page_number is what citations are built from. Storing
        chunk_index in ChromaDB metadata isn't currently needed downstream —
        it's used by ingest_pdf() purely to track sliding-window position during
        chunk construction, not as a retrieval/citation field.
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
    response = gemini_client_1.models.embed_content(
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

        # Metadata stored per chunk — enables page-level citations and
        # Phase 4's where={"file_name": ...} multi-document filtering
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
        
        # BM25 Search call
        build_bm25_index(new_chunks)
        
        return "Data ingestion complete. Document saved successfully."

    except chromadb.errors.DuplicateIDError:
        # Raised when any chunk ID already exists in the collection.
        # Entire batch is rejected — graceful message returned instead of crash.
        return "This document has already been ingested. You can start querying it directly."


# ── PHASE 2 — RETRIEVAL ───────────────────────────────────────
# ============================================================
# Build / Update BM25 Index
# ============================================================

def build_bm25_index(new_chunks):

    if not new_chunks:
        return

    global bm25_corpus, bm25_index

    # Merge new chunks into existing corpus
    for chunk in new_chunks:
        bm25_corpus[chunk["text"]] = chunk

    # Build text corpus
    full_corpus = list(bm25_corpus.keys())

    # Tokenize
    corpus_tokens = bm25s.tokenize(
        full_corpus,
        stopwords="english"
    )

    # Rebuild BM25
    bm25_index = bm25s.BM25(corpus=full_corpus)
    bm25_index.index(corpus_tokens)

    # Save BM25 index
    bm25_index.save(
        BM25_INDEX_DIR,
        corpus=full_corpus
    )

    # Save corpus dictionary
    with open(BM25_CORPUS_FILE, "w", encoding="utf-8") as file:
        json.dump(
            bm25_corpus,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(f"✅ BM25 index updated with {len(full_corpus)} chunks.")
    

def bm25_retrieve(user_query, top_k = DEFAULT_VECTOR_TOP_K  ):
    
    if not bm25_index :
        return []
    
    query_tokens = bm25s.tokenize(user_query)
    
    result, score = bm25_index.retrieve(query_tokens,k=top_k)
    
    res = {}
    for k in range(top_k):
        chunk = bm25_corpus[result[0][k]]
        
        chunk['score'] = score[0][k]
        
        res[chunk['text']] = chunk
        
    return res


def vector_retrieve( user_input: str, where: dict ) -> list:

    # Embed user question — must use same model as ingestion for valid cosine comparison
    response = gemini_client_1.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[user_input]
    )


    results = collection.query(
        query_embeddings=[response.embeddings[0].values],
        where=where,
        n_results=DEFAULT_VECTOR_TOP_K,
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    # print(results["metadatas"][0])
    if not results["documents"][0]:
        return []
    # ============================================================
    # Build candidate chunk list
    # ============================================================

    retrieved_chunks = [
        {
            "text": text,
            "metadata": metadata,
            "distance": distance,
        }
        for text, metadata, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]

    return retrieved_chunks

def query_rag(user_input: str, where: dict) -> list:
    
    vector_retrieved_chunks=vector_retrieve(user_input=user_input, where=where)

    bm25_retrieved_chunks = bm25_retrieve(user_input)
    
    if not vector_retrieved_chunks and not bm25_retrieved_chunks :
        return {"result":f"No match found for the query '{user_input}'"}
    
    filered_bm25_retrieved_chunks = {}
    
    min_score , max_score = float('inf'),float('-inf')
    for text,chunk in bm25_retrieved_chunks.items():
        if chunk['file_name'] != where['file_name']:
            continue
        filered_bm25_retrieved_chunks[text] = chunk
        
        if chunk['score'] > max_score:
            max_score = chunk['score']
        
        if chunk['score'] < min_score:
            min_score = chunk['score']
            
    # Adding vector_sim to each vector 
    for chunk in vector_retrieved_chunks:
        chunk['vector_sim'] = 1 - chunk['distance']
    
    if min_score != max_score:
        normalized = 0
        for text,chunk in filered_bm25_retrieved_chunks.items():
            normalized = ( chunk['score'] - min_score ) / ( max_score - min_score )
            chunk['normalized'] = normalized
            chunk['distance'] = 1 - chunk['normalized'] 
        
    else:
        normalized = 1
        for text,chunk in filered_bm25_retrieved_chunks.items():
            chunk['normalized'] = normalized
            chunk['distance'] = 1 - chunk['normalized']
            
            
    alpha = 0.5
    unified_chunks = {}
    
    for chunk in vector_retrieved_chunks:
        
        
        if chunk['text'] in filered_bm25_retrieved_chunks:
            chunk['fusion_score'] = ( alpha * chunk['vector_sim']) + ((1-alpha) * filered_bm25_retrieved_chunks[chunk['text']]['normalized'])
        
        else:
            chunk['fusion_score'] = (alpha * chunk['vector_sim']) + ((1-alpha) * 0)
        
        unified_chunks[chunk['text']] = chunk
        
            
    for text, chunk in filered_bm25_retrieved_chunks.items():
        
        if text in unified_chunks:
            continue
        chunk['fusion_score'] = (alpha * 0) + ((1-alpha) * chunk['normalized'])
        chunk['metadata'] = {
            "page_number": chunk["page_number"],
            "file_name": chunk["file_name"]
        }
        unified_chunks[text] = chunk 
    # ============================================================
    # CrossEncoder Reranking
    # ============================================================
        
    reranked_chunks = rerank(
        query=user_input,
        retrieved_chunks=[chunk for text,chunk in unified_chunks.items()],
        top_k=DEFAULT_RERANK_TOP_K,
    )

    return reranked_chunks


# ── PHASE 4 — DOCUMENT RELEVANCE GATING ───────────────────────

# ============================================================
# Generic Gemini Response Generator
# ============================================================

def generate_gemini_response(
    prompt: str,
    *,
    model: str = GENERATION_MODEL,
    temperature: float = 0.0,
    normalize: bool = False,
) -> str:
    """
    Generate a Gemini response using the
    dynamic API manager.

    Parameters
    ----------
    prompt
        Prompt sent to Gemini.

    model
        Gemini model.

    temperature
        Generation temperature.

    normalize
        Normalizes the response for
        classifier-style outputs.
    """

    response = gemini_generate_with_failover(

        prompt=prompt,

        model=model,

        temperature=temperature,

    )

    if normalize:

        response = (
            response
            .strip()
            .lower()
            .replace(".", "")
        )

    return response


# ============================================================
# Classifier Response Generator
# ============================================================

def generate_classifier_response(
    prompt: str,
) -> str:
    """
    Specialized wrapper used by the
    document-routing classifier.
    """

    return generate_gemini_response(

        prompt=prompt,

        model=GENERATION_MODEL,

        temperature=0.0,

        normalize=True,

    )


def classify_document_relevance(user_input: str, filenames: str) -> bool:
    """Asks Gemini whether answering the user's question actually requires
    reading the uploaded documents at all.

    Phase 4 addition. Closes a gap where the LLM would sometimes call
    search_documents() even on queries with no document reference whatsoever,
    despite the file list being visible to it via FILE_PROMPT — a prompt-rule
    non-compliance issue, not a missing-information issue. This function moves
    that decision out of the main LLM's hands entirely, into a dedicated,
    low-temperature, single-purpose classifier call.

    Parameters:
        user_input (str) → the user's current question, verbatim
        filenames  (str) → space-separated string of every filename currently
                           in the ChromaDB collection, built by get_available_files()

    Returns:
        bool → True only if the question explicitly requires retrieving
               information FROM the uploaded documents (summarize, extract,
               compare, quote, answer-about-contents). False for everything
               else, including requests that the documents COULD usefully
               inform but don't strictly require (general startup analysis,
               MVP suggestions, tech stack advice, etc.) — see the prompt's
               own TRUE/FALSE example lists for the exact boundary.

    Why temperature=0.0:
        This is a binary routing decision, not creative generation — any
        variance between identical calls is purely undesirable noise here.
        Lower temperature reduces (but per Phase 4 testing, does not fully
        eliminate) inconsistent classification on ambiguous phrasing.

    Why a separate classifier call instead of relying on FILE_PROMPT rules alone:
        FILE_PROMPT's Rule 1 already instructs the main LLM not to call
        search_documents() for non-document queries, but that instruction
        alone was not reliably followed. A dedicated classifier, asked nothing
        else, is a structurally narrower decision than asking the main LLM to
        both decide relevance AND execute the rest of the pipeline correctly
        in the same turn.

    Known limitation (Phase 4, not yet resolved):
        3 of 4 known test cases pass reliably. One ambiguous case — "analyze
        this idea with full tech stack and MVP suggestion" — intermittently
        misclassifies as True even with explicit FALSE examples and
        temperature=0.0 already in place. This is evidence that prompt-only
        classification has a real, non-zero error rate for ambiguous phrasing,
        not a bug fixable by further prompt rewrites alone. Deferred — needs a
        structural safety net eventually (e.g. a second-opinion check using
        actual retrieval similarity scores), not a fourth prompt iteration.
        See LEARNING_LOG.md Phase 4 section for full context.
    """

    prompt = f"""
You are a document-routing classifier.

Your job is to determine whether answering the user's request REQUIRES reading the uploaded documents.

IMPORTANT:

You are NOT deciding whether the documents might be useful.

You are NOT deciding whether the documents contain related information.

You are NOT deciding whether the answer could be improved by reading the documents.

You are ONLY deciding whether the user's request explicitly requires information from the uploaded documents.

---

User Query:
{user_input}

Uploaded Documents:
{filenames}

---
Return TRUE only if answering the user's request requires reading information from one or more uploaded documents.

Return FALSE if the request can be answered using general knowledge, reasoning, or by generating new content without consulting the uploaded documents.

If uploaded documents are available (indicated by a non-empty filenames list) AND the user's query refers to a specific section or structural part of a document (for example: introduction, methodology, findings, conclusion, executive summary), infer that the user is referring to the uploaded documents and return TRUE.

Do not classify a query as TRUE simply because uploaded filenames exist.

Uploaded filenames only provide evidence that documents are available. The query itself must indicate that the user is asking about the contents of those documents, either explicitly (e.g., "uploaded report", "attached PDF", "pitch deck") or implicitly through document-structural language (e.g., "methodology section", "conclusion", "findings", "executive summary").

Return TRUE only if the user is explicitly asking to:

* summarize an uploaded document
* analyze the contents of an uploaded document

* extract information from an uploaded document
* answer questions about information contained in an uploaded document
* quote, cite, or reference an uploaded document
* compare uploaded documents
* explain what an uploaded document says
* find specific information inside an uploaded document

Examples that should return TRUE:

"Summarize the uploaded PDF"
"What does the report say about revenue?"
"Extract all action items from the document"
"Compare the two uploaded files"
"What are the key findings in the report?"
"Analyze the contents of the uploaded document"
"Summarize the uploaded pitch deck"
"Extract the valuation from the uploaded term sheet"
"Compare the uploaded investor decks"
"What does the uploaded financial model predict?"
"Extract action items from the uploaded PRD"
"What does the methodology section describe?"
"Compare the introduction and conclusion."

---

Return FALSE if the user is:

* asking for general knowledge
* asking for recommendations
* asking for brainstorming
* asking for planning
* asking for strategy
* asking for advice
* asking for MVP suggestions
* asking for tech stack recommendations
* asking for startup analysis
* asking for market analysis
* asking for coding help
* asking for explanations that can be answered without reading the documents

Return FALSE even if the uploaded documents might contain relevant context.

Return FALSE even if reading the documents could improve the answer.

Return FALSE unless information must be retrieved from the uploaded documents to satisfy the request.

Examples that should return FALSE:

"Suggest a tech stack for my startup"
"Analyze this startup idea"
"Give me MVP recommendations"
"How should I market this product?"
"What is the weather today?"
"Explain machine learning"
"Write a business plan"
"Generate feature ideas"
"Create a pitch deck"
"Write a business plan"
"Draft a term sheet"
"Create an investor deck"
"Build a financial model"
"What is a methodology?"
"What is a pitch deck?"
"What is a financial model?"

Even if a pitch deck, report, notes, or other related documents are uploaded, these examples remain FALSE because the request does not require retrieving information from those documents.

---

Decision Rule:

Ask yourself:

"Can I answer this request without opening or reading any uploaded document?"

If YES → return FALSE

If NO → return TRUE

---

Output Requirements:

Return ONLY:

true

OR

false

No punctuation.
No markdown.
No explanations.
"""
        # ========================================================
    # Execute Document Classifier
    # ========================================================

    start_time = time.perf_counter()

    try:

        response_text = generate_classifier_response(
            prompt=prompt,
        )

        prediction = (
            response_text == "true"
        )

        latency = (
            time.perf_counter()
            - start_time
        )

        print()

        print("=" * 70)
        print("DOCUMENT CLASSIFIER")
        print("=" * 70)

        print(
            f"Query      : {user_input}"
        )

        print(
            f"Prediction : {response_text.upper()}"
        )

        print(
            f"Requires RAG : {prediction}"
        )

        print(
            f"Latency    : {latency:.3f}s"
        )

        print("=" * 70)
        print()

        return prediction

    except RuntimeError as error:

        latency = (
            time.perf_counter()
            - start_time
        )

        print()

        print("=" * 70)
        print("DOCUMENT CLASSIFIER ERROR")
        print("=" * 70)

        print(error)

        print(
            f"Latency : {latency:.3f}s"
        )

        print("=" * 70)
        print()

        raise

    except Exception as error:

        latency = (
            time.perf_counter()
            - start_time
        )

        print()

        print("=" * 70)
        print("DOCUMENT CLASSIFIER ERROR")
        print("=" * 70)

        print(type(error).__name__)

        print(error)

        print(
            f"Latency : {latency:.3f}s"
        )

        print("=" * 70)
        print()

        raise


def get_available_files(user_input: str) -> str:
    """Returns the live list of uploaded filenames, but ONLY if the current
    question actually requires reading them.

    This is the function orchestrator.py's run() calls every single turn to
    build current_files. The result of this call is what determines whether
    Stage 4 exists at all for that turn, and whether FILE_PROMPT gets injected
    into temp_list[0] — see orchestrator.py's run() docstring for how that
    injection works.

    Parameters:
        user_input (str) → the user's current question, verbatim. Required
                           Phase 4 signature change — earlier versions of this
                           function took no arguments and simply returned
                           every filename in the collection unconditionally,
                           which is what originally let the LLM call
                           search_documents() on completely unrelated queries.

    Returns:
        str → space-separated string of every filename in the ChromaDB
              collection, if classify_document_relevance() returns True for
              this question. Returns "" (empty string) if no files have ever
              been ingested, OR if files exist but this particular question
              doesn't require reading them.

    Why early-exit on empty collection before calling the classifier:
        If nothing has ever been ingested, there's no need to spend a Gemini
        API call asking "is this question about documents" — there are no
        documents to be about. Saves a call and avoids a meaningless
        classification on every single turn of a session with no uploads.

    Why set() before list() on the filenames:
        collection.get(include=["metadatas"]) returns one metadata dict per
        CHUNK, not per file — a single ingested PDF easily produces dozens of
        chunks, all sharing the same file_name. set() deduplicates down to the
        actual distinct files before building the classifier's filename list.
    """

    result = collection.get(include=["metadatas"])

    # ============================================================
    # Extract Unique Filenames
    # ============================================================

    unique_filenames = sorted(

        {

            metadata["file_name"]

            for metadata in result["metadatas"]

            if metadata
            and metadata.get("file_name")

        }

    )

    # Early exit: no files in collection — nothing to classify against
    if not unique_filenames:
        return ""

    # Build filename list for Gemini classification
    file_list = " ".join(unique_filenames)

    print()

    print("=" * 70)
    print("AVAILABLE DOCUMENTS")
    print("=" * 70)

    print(f"Total Files : {len(unique_filenames)}")

    for filename in unique_filenames:

        print(f"• {filename}")

    print("=" * 70)
    print()
    
    # Ask Gemini: does THIS question actually require reading these documents?
    is_doc_query = classify_document_relevance(
        user_input=user_input,
        filenames=file_list
    )

    if is_doc_query:
        return "\n".join(unique_filenames)

    return ""

# ── MANUAL BATCH RE-INGESTION (developer use only) ─────────────
# Guarded behind __main__ — importing rag.py anywhere else (the app, tools.py,
# the evaluator) will NOT trigger this block. Without this guard, every import
# of this module would silently re-ingest all 12 files below on every run —
# this was a real bug caught during Phase 4 decoration, not a hypothetical one.
#
# Run directly to bulk re-ingest the full test/demo corpus, e.g. after
# deleting data/chroma_db/ to rebuild from a clean state:
#   python -m src.rag.rag

if __name__ == "__main__":

    file_paths = [
        r'data\uploads\CivicLaw_Pro.pdf',
        r'data\uploads\HealthAssist_AI.pdf',
        r'data\uploads\LegalAid_AI.pdf',
        r'data\uploads\PoliceConnect_AI.pdf',
        r'data\uploads\PolicyInsight_AI.pdf',
        r'data\uploads\TechStack_Genius.pdf',
        r'data\uploads\combined_150_questions.pdf',
        r'data\uploads\01_Artificial_General_Intelligence_Report.pdf',
        r'data\uploads\02_Cybersecurity_Threat_Intelligence_Report.pdf',
        r'data\uploads\03_Quantum_Computing_Research_Report.pdf',
        r'data\uploads\04_Renewable_Energy_Transition_Report.pdf',
        r'data\uploads\05_Climate_Change_Mitigation_Report.pdf',
    ]

    for file in file_paths:
        chunks = ingest_pdf(file)
        embed_and_store(chunks)