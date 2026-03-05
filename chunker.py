"""
chunker.py — Text Cleaning & Chunking Module
---------------------------------------------
Takes raw OCR output (noisy, messy handwriting text) and:
  1. Cleans up common OCR artifacts
  2. Splits text into small, semantically coherent chunks
  3. Attaches metadata (page number, chunk ID) to each chunk

Each chunk is a dict:
    {
        "chunk_id": int,
        "page": int,
        "text": str
    }
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# ── CLEANING CONSTANTS ────────────────────────────────────────────────────────

# Characters that Tesseract commonly misreads in handwriting
OCR_NOISE_PATTERNS = [
    (r"[|]{2,}", " "),          # Repeated pipe chars (scan artifacts)
    (r"[~`]{2,}", " "),         # Repeated tildes/backticks
    (r"[_]{3,}", " "),          # Long underscores (underline artifacts)
    (r"\s{3,}", " "),           # Collapse 3+ spaces to single space
    (r"\n{4,}", "\n\n"),        # Collapse excessive blank lines
    (r"[^\x00-\x7F]+", " "),    # Remove non-ASCII garbage (common in scan OCR)
    (r"(?<!\w)\.{3,}(?!\w)", ""),  # Standalone ellipsis artifacts
]

# Minimum characters for a chunk to be considered meaningful
MIN_CHUNK_LENGTH = 30

# Target chunk size in characters (aim for ~200 chars per chunk for RAG)
CHUNK_SIZE = 400

# Overlap between consecutive chunks (helps preserve context across boundaries)
CHUNK_OVERLAP = 80


def clean_ocr_text(raw_text: str) -> str:
    """
    Clean OCR output text by removing noise, fixing whitespace,
    and normalizing common Tesseract artifacts.

    Args:
        raw_text: Raw string returned by Tesseract.

    Returns:
        A cleaner string with reduced noise.
    """
    if not raw_text:
        return ""

    text = raw_text

    # Apply all noise-removal patterns
    for pattern, replacement in OCR_NOISE_PATTERNS:
        text = re.sub(pattern, replacement, text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Fix common OCR letter confusion in context
    # (These are conservative; full correction requires NLP)
    text = re.sub(r"\b0(?=[a-zA-Z])", "O", text)   # 0ld → Old
    text = re.sub(r"(?<=[a-zA-Z])0\b", "o", text)  # hell0 → hello
    text = re.sub(r"\bl\b", "I", text)             # Standalone l → I
    text = re.sub(r"\b1\b(?=\s+[a-zA-Z])", "I", text)  # 1 am → I am

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def _split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentence-like segments using punctuation and newlines.
    Handwriting OCR often lacks punctuation, so we also split on newlines.

    Args:
        text: Cleaned text string.

    Returns:
        List of sentence strings.
    """
    # Split on sentence-ending punctuation followed by whitespace or end
    # Also split on double newlines (paragraph breaks common in notes)
    segments = re.split(r"(?<=[.!?])\s+|\n{2,}", text)
    
    # Further split very long lines on single newlines
    result = []
    for seg in segments:
        if len(seg) > CHUNK_SIZE * 2:
            # Long segment — split on single newlines as fallback
            sub_segs = seg.split("\n")
            result.extend([s.strip() for s in sub_segs if s.strip()])
        else:
            if seg.strip():
                result.append(seg.strip())

    return result


def _build_chunks_with_overlap(
    sentences: List[str],
    page: int,
    chunk_id_start: int
) -> List[Dict]:
    """
    Build overlapping text chunks from a list of sentences.

    Uses a sliding window approach:
      - Keep adding sentences until the chunk exceeds CHUNK_SIZE
      - Then start a new chunk, but carry over CHUNK_OVERLAP characters
        from the end of the previous chunk

    Args:
        sentences: List of sentence strings for a single page.
        page: Page number these sentences came from.
        chunk_id_start: Starting chunk ID counter for this page.

    Returns:
        List of chunk dicts with keys: chunk_id, page, text.
    """
    chunks = []
    current_chunk_parts = []
    current_length = 0
    chunk_id = chunk_id_start

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_length + sentence_len > CHUNK_SIZE and current_chunk_parts:
            # Finalize current chunk
            chunk_text = " ".join(current_chunk_parts).strip()
            if len(chunk_text) >= MIN_CHUNK_LENGTH:
                chunks.append({
                    "chunk_id": chunk_id,
                    "page": page,
                    "text": chunk_text
                })
                chunk_id += 1

            # Overlap: carry last N chars into the next chunk
            overlap_text = chunk_text[-CHUNK_OVERLAP:]
            current_chunk_parts = [overlap_text, sentence] if overlap_text.strip() else [sentence]
            current_length = len(overlap_text) + sentence_len
        else:
            current_chunk_parts.append(sentence)
            current_length += sentence_len + 1  # +1 for space

    # Flush remaining sentences as the last chunk
    if current_chunk_parts:
        chunk_text = " ".join(current_chunk_parts).strip()
        if len(chunk_text) >= MIN_CHUNK_LENGTH:
            chunks.append({
                "chunk_id": chunk_id,
                "page": page,
                "text": chunk_text
            })

    return chunks


def clean_and_chunk_text(pages: List[Dict]) -> List[Dict]:
    """
    Main entry point: clean OCR text from all pages and split into chunks.

    Args:
        pages: List of dicts from ocr_reader.extract_text_from_pdf():
                   [{"page": 1, "text": "..."}, ...]

    Returns:
        Flat list of chunk dicts:
            [
                {"chunk_id": 0, "page": 1, "text": "..."},
                {"chunk_id": 1, "page": 1, "text": "..."},
                {"chunk_id": 2, "page": 2, "text": "..."},
                ...
            ]
    """
    all_chunks = []
    global_chunk_id = 0

    for page_data in pages:
        page_num = page_data["page"]
        raw_text = page_data.get("text", "")

        if not raw_text or not raw_text.strip():
            logger.debug(f"Page {page_num}: empty text, skipping.")
            continue

        # Step 1: Clean
        cleaned = clean_ocr_text(raw_text)
        if not cleaned:
            logger.debug(f"Page {page_num}: text became empty after cleaning, skipping.")
            continue

        logger.debug(f"Page {page_num}: {len(raw_text)} → {len(cleaned)} chars after cleaning.")

        # Step 2: Sentence segmentation
        sentences = _split_into_sentences(cleaned)
        if not sentences:
            # Fallback: treat entire page as one chunk
            sentences = [cleaned]

        logger.debug(f"Page {page_num}: {len(sentences)} sentence segment(s).")

        # Step 3: Build overlapping chunks
        page_chunks = _build_chunks_with_overlap(sentences, page_num, global_chunk_id)
        
        if not page_chunks and cleaned:
            # Absolute fallback: if we have text but no chunks formed (e.g., short page)
            page_chunks = [{
                "chunk_id": global_chunk_id,
                "page": page_num,
                "text": cleaned[:CHUNK_SIZE]
            }]

        all_chunks.extend(page_chunks)
        global_chunk_id += len(page_chunks)

        logger.info(f"Page {page_num}: created {len(page_chunks)} chunk(s).")

    logger.info(f"Total chunks created: {len(all_chunks)}")
    return all_chunks
