"""
utils.py — Shared Utilities
----------------------------
Helper functions used across the application:
  - Logging setup
  - Terminal display (banners, separators)
  - Saving extracted text to disk
  - Misc helpers
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Dict


def setup_logging(level_str: str = "INFO"):
    """
    Configure root logger with a clean format for terminal output.
    Only WARNING+ messages go to stderr; INFO goes to stdout.

    Args:
        level_str: One of "DEBUG", "INFO", "WARNING", "ERROR".
    """
    level = getattr(logging, level_str.upper(), logging.INFO)

    # Formatter — concise for INFO, detailed for DEBUG
    if level <= logging.DEBUG:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        datefmt = "%H:%M:%S"
    else:
        fmt = "[%(levelname)s] %(message)s"
        datefmt = None

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    # Silence noisy third-party loggers
    for noisy_lib in ("sentence_transformers", "transformers", "faiss", "PIL", "tqdm"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)


def print_banner():
    """Print a stylized application banner to the terminal."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║          📝 Handwritten PDF Q&A System (RAG)                 ║
║      OCR + Embeddings + FAISS + Local LLM (Ollama)           ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_separator(char: str = "─", width: int = 64):
    """Print a horizontal separator line."""
    print(char * width)


def save_extracted_text(pages: List[Dict], output_path: str):
    """
    Save OCR-extracted text from all pages to a plain text file.
    Useful for debugging OCR quality before indexing.

    Args:
        pages: List of {"page": int, "text": str} dicts from ocr_reader.
        output_path: File path to write (e.g., "notes_extracted.txt").
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for page_data in pages:
                f.write(f"{'='*60}\n")
                f.write(f"PAGE {page_data['page']}\n")
                f.write(f"{'='*60}\n")
                f.write(page_data.get("text", "") + "\n\n")
        logging.getLogger(__name__).debug(f"Extracted text saved to: {output_path}")
    except IOError as e:
        logging.getLogger(__name__).warning(f"Could not save extracted text: {e}")


def confirm_prompt(message: str, default: bool = True) -> bool:
    """
    Show a yes/no confirmation prompt in the terminal.

    Args:
        message: The question to display.
        default: Default choice if user presses Enter without typing.

    Returns:
        True if user confirmed, False otherwise.
    """
    hint = "[Y/n]" if default else "[y/N]"
    try:
        response = input(f"{message} {hint}: ").strip().lower()
        if not response:
            return default
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return default


def truncate_text(text: str, max_chars: int = 200) -> str:
    """
    Truncate a string to a maximum length with an ellipsis.
    Useful for displaying chunk previews in the terminal.

    Args:
        text: Input string.
        max_chars: Maximum characters to show.

    Returns:
        Possibly truncated string.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 3] + "..."


def check_dependency(command: str, install_hint: str) -> bool:
    """
    Check if a system command (like `tesseract` or `ollama`) is available on PATH.

    Args:
        command: The command name to test (e.g., "tesseract").
        install_hint: Message to display if not found.

    Returns:
        True if found, False otherwise.
    """
    import shutil
    found = shutil.which(command) is not None
    if not found:
        logging.getLogger(__name__).warning(
            f"'{command}' not found in PATH. {install_hint}"
        )
    return found


def format_sources(source_pages: List[int]) -> str:
    """
    Format a list of page numbers into a readable string.

    Args:
        source_pages: List of page number integers.

    Returns:
        Formatted string like "Page 1, Page 3" or "No sources."
    """
    if not source_pages:
        return "No sources."
    return ", ".join(f"Page {p}" for p in sorted(set(source_pages)))
