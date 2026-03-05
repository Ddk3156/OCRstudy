"""
main.py — Entry point for Handwritten PDF RAG System
-----------------------------------------------------
Orchestrates the full pipeline:
  1. OCR extraction from PDF
  2. Text cleaning & chunking
  3. Embedding generation
  4. FAISS vector store indexing
  5. Interactive Q&A loop
"""

import os
import sys
import argparse
import logging
from pathlib import Path

from ocr_reader import extract_text_from_pdf
from chunker import clean_and_chunk_text
from embeddings import EmbeddingModel
from vector_store import VectorStore
from qa_engine import QAEngine
from utils import setup_logging, print_banner, print_separator, save_extracted_text

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Handwritten PDF Q&A System using OCR + RAG"
    )
    parser.add_argument(
        "--pdf",
        type=str,
        help="Path to the handwritten PDF file",
        default=None
    )
    parser.add_argument(
        "--index",
        type=str,
        help="Path to load an existing FAISS index (skip OCR step)",
        default=None
    )
    parser.add_argument(
        "--save-index",
        type=str,
        help="Path to save the FAISS index after indexing",
        default="notes_index"
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Ollama model to use for answer generation (default: mistral)",
        default="mistral"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        help="Number of chunks to retrieve (default: 3)",
        default=3
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity level"
    )
    return parser.parse_args()


def build_index(pdf_path: str, save_index_path: str, embedding_model: EmbeddingModel) -> VectorStore:
    """
    Full pipeline: PDF → OCR → Chunk → Embed → FAISS index.
    
    Args:
        pdf_path: Path to the input PDF file.
        save_index_path: Directory path to save the built index.
        embedding_model: Initialized EmbeddingModel instance.
        
    Returns:
        A populated VectorStore instance.
    """
    logger = logging.getLogger(__name__)

    # ── STEP 1: OCR ──────────────────────────────────────────────────────────
    print_separator()
    print("📄 STEP 1/4 — Extracting text from PDF via OCR...")
    pages = extract_text_from_pdf(pdf_path)

    if not pages:
        print("❌ OCR returned no text. Please check the PDF and Tesseract installation.")
        sys.exit(1)

    # Optionally save extracted text for inspection
    extracted_path = Path(pdf_path).stem + "_extracted.txt"
    save_extracted_text(pages, extracted_path)
    print(f"   ✅ OCR complete — {len(pages)} page(s) extracted. Saved to: {extracted_path}")

    # ── STEP 2: CLEAN & CHUNK ─────────────────────────────────────────────────
    print_separator()
    print("✂️  STEP 2/4 — Cleaning and chunking text...")
    chunks = clean_and_chunk_text(pages)

    if not chunks:
        print("❌ No chunks created. The extracted text may be empty.")
        sys.exit(1)

    print(f"   ✅ Created {len(chunks)} chunk(s) ready for indexing.")

    # ── STEP 3: EMBEDDINGS ────────────────────────────────────────────────────
    print_separator()
    print("🔢 STEP 3/4 — Generating embeddings...")
    texts = [c["text"] for c in chunks]
    embeddings = embedding_model.encode(texts)
    print(f"   ✅ Embeddings generated — shape: {embeddings.shape}")

    # ── STEP 4: VECTOR STORE ──────────────────────────────────────────────────
    print_separator()
    print("🗃️  STEP 4/4 — Building FAISS index...")
    vector_store = VectorStore(dimension=embeddings.shape[1])
    vector_store.add(embeddings, chunks)

    # Save index for reuse
    vector_store.save(save_index_path)
    print(f"   ✅ Index built and saved to: '{save_index_path}/'")

    return vector_store


def load_index(index_path: str, embedding_model: EmbeddingModel) -> VectorStore:
    """
    Load an existing FAISS index from disk.
    
    Args:
        index_path: Directory where the index was previously saved.
        embedding_model: Initialized EmbeddingModel instance (needed for dim).
        
    Returns:
        A loaded VectorStore instance.
    """
    print(f"📂 Loading existing index from '{index_path}'...")
    vector_store = VectorStore(dimension=embedding_model.get_dimension())
    vector_store.load(index_path)
    print(f"   ✅ Loaded {vector_store.size()} chunk(s) from index.")
    return vector_store


def run_qa_loop(qa_engine: QAEngine, top_k: int):
    """
    Interactive terminal Q&A loop.
    Keeps running until the user types 'exit' or 'quit'.
    
    Args:
        qa_engine: Initialized QAEngine instance.
        top_k: Number of top chunks to retrieve per question.
    """
    print_separator()
    print("💬 Q&A MODE — Type your question below.")
    print("   Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            question = input("❓ Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Exiting. Goodbye!")
            break

        if not question:
            continue

        if question.lower() in ("exit", "quit", "q"):
            print("\n👋 Exiting. Goodbye!")
            break

        print("\n⏳ Searching notes and generating answer...\n")

        result = qa_engine.answer(question, top_k=top_k)

        print("─" * 60)
        print(f"📝 Answer:\n{result['answer']}")
        print()
        if result["sources"]:
            source_pages = ", ".join(f"Page {s}" for s in sorted(set(result["sources"])))
            print(f"📚 Sources: {source_pages}")
        print("─" * 60)
        print()


def main():
    args = parse_args()
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    print_banner()

    # Validate input: need either a PDF or an existing index
    if not args.pdf and not args.index:
        pdf_path = input("📂 Enter path to your handwritten PDF: ").strip()
        if not pdf_path:
            print("❌ No PDF path provided. Exiting.")
            sys.exit(1)
        args.pdf = pdf_path

    if args.pdf and not os.path.isfile(args.pdf):
        print(f"❌ File not found: {args.pdf}")
        sys.exit(1)

    # ── LOAD EMBEDDING MODEL ──────────────────────────────────────────────────
    print_separator()
    print("🤖 Loading local embedding model (sentence-transformers)...")
    embedding_model = EmbeddingModel()
    print("   ✅ Embedding model ready.")

    # ── BUILD OR LOAD INDEX ───────────────────────────────────────────────────
    if args.index:
        vector_store = load_index(args.index, embedding_model)
    else:
        vector_store = build_index(args.pdf, args.save_index, embedding_model)

    # ── INIT QA ENGINE ────────────────────────────────────────────────────────
    print_separator()
    print(f"🧠 Initializing QA engine with model: '{args.model}'...")
    qa_engine = QAEngine(
        vector_store=vector_store,
        embedding_model=embedding_model,
        ollama_model=args.model
    )
    print("   ✅ QA engine ready.")

    # ── START CONVERSATION LOOP ───────────────────────────────────────────────
    run_qa_loop(qa_engine, top_k=args.top_k)


if __name__ == "__main__":
    main()
