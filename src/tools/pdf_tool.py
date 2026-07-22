import os 
import json
import pdfplumber
import reportlab
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from src.config.settings import (
    PDF_OUTPUT_DIR,
    CHUNK_SIZE,
    STEP,
    MIN_CHUNK_WORDS,
    
)

def read_pdf(file_path: str) -> list:
    

    file_name = os.path.basename(file_path)  # strip directory path — store filename only
    
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

   

    # Guard against empty chunks list — max() on an empty generator raises
    # ValueError, which would crash ingestion for an all-image/scanned PDF
    # with no extractable text on any page, instead of returning [] cleanly.
    

    return chunks

def write_pdf(content:str)->str:
    os.makedirs(PDF_OUTPUT_DIR,exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"report_{timestamp}.pdf"
    file_path = os.path.join(PDF_OUTPUT_DIR,file_name)
    doc = SimpleDocTemplate(
        filename=file_path,
    )
    
    styles = getSampleStyleSheet()
        
    elements = [
        Paragraph(line,styles["Normal"])
        for line in content.split("\n")
        
    ]
    
    doc.build(elements)
    
    
    
    return file_path


if __name__ == "__main__":
    pdf_path = write_pdf("Hello World!\nThis is a simple test workflow.")
    chunks = read_pdf(pdf_path)
    print(chunks)