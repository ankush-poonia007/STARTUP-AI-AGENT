# ============================================================
#  rag.py — Retrieval Augmented Generation Pipeline for BizRadar AI
# ============================================================
#
#  What this file does:
#  Implements the complete two-phase RAG pipeline for BizRadar AI, plus the
#  Phase 4 document-relevance classification layer used to decide whether
#  Stage 4 should be unlocked for a given turn at all.
#
#  Phase 1 — Ingestion (runs once per document):
#      PDF → paragraph-aware fixed-token chunks → Gemini embeddings → ChromaDB
#  Phase 2 — Retrieval (runs on every user query):
#      User question → Gemini embedding → cosine similarity search,
#      scoped by where={"file_name": ...} → top 3 chunks
#  Phase 4 addition — Relevance Gating (runs once per conversation turn):
#      User question → is ANY uploaded file relevant to this question? →
#      real filenames returned only if yes, "" otherwise
#
#  What this file does NOT handle:
#  Does not manage conversation history — that belongs to context_manager.py.
#  Does not call the LLM for final answer generation — that belongs to
#  orchestrator.py.
#  Does not define the search_documents tool wrapper — that belongs to tools.py.
#
#  Functions:
#  - ingest_pdf()                  → PDF file path → flat list of chunk dicts
#  - embed_and_store()              → chunk list → vectors stored in ChromaDB
#  - query_rag()                    → question + where filter → top 3 chunks + metadata
#  - classify_document_relevance()  → Phase 4: Gemini true/false call deciding whether
#                                      a question actually requires reading the
#                                      uploaded documents at all
#  - get_available_files()          → Phase 4: wraps classify_document_relevance() —
#                                      returns real filenames only when relevant,
#                                      "" otherwise. This is what orchestrator.py's
#                                      run() actually calls each turn to decide
#                                      whether Stage 4 exists for that turn.
#
#  Used by:
#  - app.py          → calls ingest_pdf() + embed_and_store() at startup if user uploads a PDF
#  - tools.py        → calls query_rag() inside search_documents() tool function
#  - orchestrator.py → calls get_available_files(user_input) each turn to build
#                      current_files before deciding whether to inject FILE_PROMPT
#                      and whether Stage 4 is reachable that turn
#
#  Design Decisions:
#  - PersistentClient: data survives between sessions — Client() would lose data on exit
#  - gemini-embedding-001: stable production embedding model available on free tier API keys.
#                          Same model used for both ingestion and querying — vector space consistency.
#                          text-embedding-004 was unavailable on this API key version (404 NOT_FOUND).
#  - MD5 hash as chunk ID: prevents duplicate ingestion even if the same PDF is renamed
#  - Paragraph-aware fixed-token chunking (Phase 4): replaced pure \n\n splitting.
#                          Small paragraphs kept whole; large paragraphs split via a
#                          sliding window (CHUNK_SIZE=250, OVERLAP=50, STEP=200).
#                          Pure \n\n splitting under-chunked dense PDFs — a 2-page report
#                          previously produced only 2 chunks total. The sliding window
#                          fix was verified via evaluator.py: 100% recall@3 maintained
#                          post-migration, with properly granular chunks.
#  - Metadata stored per chunk: enables page-level citations AND Phase 4's
#                          where={"file_name": ...} filtering for multi-document isolation
#  - n_results=3: reduced from 5 — prevents Stage 4 RAG results from bloating self.messages
#                 context and crowding out Stage 2/3 reasoning room in the agent loop
#  - heartbeat() check: verifies ChromaDB connection before attempting ingestion
#  - Two separate Gemini clients (gemini_client_1, gemini_client_2): spreads
#                          embedding calls and classifier calls across separate
#                          API keys/quotas, same rationale as tools.py's per-tool
#                          dedicated clients — see that file's header.
#
#  Phase 4 backlog note:
#  classify_document_relevance()'s ~100-line prompt is currently hardcoded inline
#  in this file, duplicating the pattern prompts.py already established for
#  SYSTEM_PROMPT/FILE_PROMPT. Deliberately left as-is for now rather than
#  refactored into prompts.py as a CLASSIFIER_PROMPT constant — flagged here so
#  it isn't forgotten, not because it's correct long-term. Revisit if/when
#  prompts.py is the established single source of truth for all LLM-facing
#  prompt strings in this codebase.
# ============================================================

import os
import hashlib

import chromadb
import pdfplumber
from google import genai
from dotenv import load_dotenv
from google.genai import types


# ── ENVIRONMENT & CLIENT SETUP ────────────────────────────────
# Runs once at module load — clients reused across all function calls.
# load_dotenv() must run before os.getenv() to populate the environment.

load_dotenv()
GEMINI_API_KEY_1  = os.getenv("GEMINI_API_KEY_1")
GEMINI_API_KEY_2  = os.getenv("GEMINI_API_KEY_2")
GEMINI_API_KEY_3  = os.getenv("GEMINI_API_KEY_3")
GEMINI_API_KEY_4  = os.getenv("GEMINI_API_KEY_4")
GEMINI_API_KEY_5  = os.getenv("GEMINI_API_KEY_5")
GEMINI_API_KEY_6  = os.getenv("GEMINI_API_KEY_6")
GEMINI_API_KEY_7  = os.getenv("GEMINI_API_KEY_7")
GEMINI_API_KEY_8  = os.getenv("GEMINI_API_KEY_8")
GEMINI_API_KEY_9  = os.getenv("GEMINI_API_KEY_9")
GEMINI_API_KEY_10 = os.getenv("GEMINI_API_KEY_10")

# gemini_client_1 → embed_content() calls (embed_and_store, query_rag)
# gemini_client_2 → generate_content() calls (classify_document_relevance)
# Split across two keys for the same reason tools.py dedicates a separate
# client per tool — spreads load across separate free-tier quotas.
gemini_client_1 = genai.Client(api_key=GEMINI_API_KEY_7)
gemini_client_2 = genai.Client(api_key=GEMINI_API_KEY_8)

# Embedding model used for both ingestion and retrieval.
# Must stay identical across both phases — changing this after ingestion
# requires deleting data/chroma_db/ and re-ingesting all documents.
# gemini-embedding-001 chosen over text-embedding-004 — 404 on this API key version.
EMBEDDING_MODEL = "gemini-embedding-001"

# PersistentClient writes to disk — data survives between sessions.
# get_or_create_collection: safe to call on every restart, no crash if collection exists.
client     = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_or_create_collection(name="data_storage")


# ── PHASE 1a — PDF INGESTION ──────────────────────────────────

def ingest_pdf(file_path: str) -> list:
    """Extract and chunk text from a PDF file for RAG ingestion.

    Opens the PDF page by page, extracts plain text, splits into
    paragraph-level units, then applies fixed-token sliding-window chunking
    to any paragraph too large to keep whole. Returns a flat list of chunk
    dicts with page/file metadata.

    Parameters:
        file_path (str) → absolute or relative path to the PDF file

    Returns:
        list → flat list of dicts, each with keys:
               - "text"        (str)  → chunk content
               - "page_number" (int)  → 1-indexed page the chunk came from
               - "file_name"   (str)  → basename of the source file (no directory path)
               - "chunk_index" (int)  → 0-indexed position of this chunk within its page
               Returns [] if the PDF has no extractable text on any page
               (e.g. a fully image-based/scanned PDF with no OCR layer).

    Why paragraph-first, then fixed-token sliding window (Phase 4 improvement):
        Pure \\n\\n paragraph splitting alone under-chunked dense PDFs — a
        2-page report could produce only 2 total chunks if each page's text
        happened to contain few paragraph breaks, losing retrieval granularity.
        Small paragraphs (≤ CHUNK_SIZE words) are kept whole, since each
        typically contains one complete idea — a meaningful retrieval unit.
        Large paragraphs are split via a sliding window so no single chunk
        becomes too large to embed meaningfully, while OVERLAP preserves
        context across the cut point so an idea spanning a chunk boundary
        isn't lost entirely from either chunk.

    Why pdfplumber over PyPDF2:
        pdfplumber handles complex PDF layouts (tables, columns, multi-font
        pitch decks) more reliably than PyPDF2, which can scramble reading
        order on non-linear layouts.

    Why the max() length-check guards against an empty chunks list:
        An all-image or otherwise non-extractable PDF produces zero chunks.
        Calling max() on an empty generator raises ValueError — this would
        crash ingestion entirely instead of returning a clear empty result
        the caller (embed_and_store, or app.py) can handle gracefully.
    """

    file_name = os.path.basename(file_path)  # strip directory path — store filename only

    CHUNK_SIZE = 250
    OVERLAP    = 50
    STEP       = CHUNK_SIZE - OVERLAP

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
        return "Data ingestion complete. Document saved successfully."

    except chromadb.errors.DuplicateIDError:
        # Raised when any chunk ID already exists in the collection.
        # Entire batch is rejected — graceful message returned instead of crash.
        return "This document has already been ingested. You can start querying it directly."


# ── PHASE 2 — RETRIEVAL ───────────────────────────────────────

def query_rag(user_input: str, where: dict) -> list:
    """Convert a user question to a vector and retrieve the top 3 relevant chunks
    from one specific document.

    Embeds the user question using the same model used during ingestion (vector
    space consistency), queries ChromaDB via cosine similarity scoped by the
    where filter, and returns matched chunks with their source metadata for
    citation.

    Parameters:
        user_input (str)  → raw user question or search query
        where      (dict) → Phase 4 addition. ChromaDB metadata filter, e.g.
                            {"file_name": "LegalAid_AI.pdf"} — restricts the
                            similarity search to chunks from one specific
                            uploaded document, even when multiple documents
                            share the same collection. This is the actual
                            mechanism that makes multi-document isolation work:
                            without it, a query could return chunks from ANY
                            uploaded PDF regardless of which one the user
                            actually meant.

    Returns:
        list → list of dicts, each with keys:
               - "text"     (str)  → matched chunk content
               - "metadata" (dict) → {"page_number": int, "file_name": str}

    Why same embedding model as embed_and_store():
        Vector space consistency — different models produce different dimensional spaces.
        Comparing vectors from different models produces meaningless similarity scores.
        Both phases use EMBEDDING_MODEL constant — single source of truth.
        Changing the model requires deleting data/chroma_db/ and re-ingesting.

    Why [response.embeddings[0].values]:
        ChromaDB expects query_embeddings as a list of float lists — one per query.
        response.embeddings returns a list of ContentEmbedding objects, not raw floats.
        .values extracts the float list. Wrapped in [] for single-query format ChromaDB expects.

    Why n_results=3 (reduced from 5):
        search_documents() is called as Stage 4, after Stages 1-3 have already populated
        self.messages with substantial context. Top-5 chunks bloated the message history
        and crowded out the LLM's reasoning room for final answer generation.
        Top-3 preserves enough context for citation and answer quality.
        Verified via evaluator.py: 100% recall@3 across 25 ground-truth questions
        spanning 5 documents — top-3 is sufficient at the current chunking granularity.

    Why zip(documents, metadatas):
        ChromaDB returns documents and metadatas as separate parallel lists under [0].
        zip() pairs each chunk with its metadata — enables source citations in agent responses.
    """

    # Embed user question — must use same model as ingestion for valid cosine comparison
    response = gemini_client_1.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=[user_input]
    )

    # ChromaDB cosine similarity search — returns nested lists, [0] for single query.
    # response.embeddings[0].values extracts raw float list from ContentEmbedding object.
    # Wrapped in [] — ChromaDB expects list of embeddings, one per query.
    # where filter scopes the search to one document — the Phase 4 isolation mechanism.
    results = collection.query(
        query_embeddings=[response.embeddings[0].values],
        where=where,
        n_results=3
    )

    print(results["metadatas"][0])

    # Pair each chunk text with its metadata — enables page-level source citations
    return [
        {"text": text, "metadata": metadata}
        for text, metadata in zip(results["documents"][0], results["metadatas"][0])
    ]


# ── PHASE 4 — DOCUMENT RELEVANCE GATING ───────────────────────

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

Even if a pitch deck, report, notes, or other related documents are uploaded, these examples remain FALSE because the request does not require retrieving information from those documents.

---

Decision Rule:

Ask yourself:

"Can I answer this request without opening or reading any uploaded document?"

If YES → return FALSE

If NO → return TRUE

---

Output Requirements:

Return exactly one word:

true

or

false

Do not provide explanations.
Do not provide reasoning.
Do not provide additional text.
"""

    response = gemini_client_2.models.generate_content(
        contents=prompt,
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            temperature=0.0
        )
    )

    response_text = response.text.strip().lower().replace(".", "")

    print(f"[DOC CLASSIFIER] Response: {response_text.capitalize()}")

    return response_text == "true"


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

    unique_filenames = list(
        set(metadata["file_name"] for metadata in result["metadatas"])
    )

    # Early exit: no files in collection — nothing to classify against
    if not unique_filenames:
        return ""

    # Build filename list for Gemini classification
    file_list = " ".join(unique_filenames)

    # Ask Gemini: does THIS question actually require reading these documents?
    is_doc_query = classify_document_relevance(
        user_input=user_input,
        filenames=file_list
    )

    if is_doc_query:
        return file_list

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