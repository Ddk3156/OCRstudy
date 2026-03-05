"""
embeddings.py — Local Embedding Model Module
---------------------------------------------
Uses sentence-transformers (all-MiniLM-L6-v2) to generate dense vector
embeddings for text chunks. Runs 100% locally — no internet required
after the model is downloaded on first use.

Model: all-MiniLM-L6-v2
  - 384-dimensional embeddings
  - Fast inference (~14K sentences/sec on CPU)
  - Strong semantic similarity for English text
  - ~80MB download (cached locally after first use)
"""

import logging
import sys
from typing import List

import numpy as np
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Default model — small, fast, good quality
DEFAULT_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Batch size for encoding — reduce if running out of RAM
ENCODING_BATCH_SIZE = 64


class EmbeddingModel:
    """
    Wrapper around sentence-transformers for encoding text into vectors.

    Usage:
        model = EmbeddingModel()
        embeddings = model.encode(["sentence 1", "sentence 2"])
        # → numpy array of shape (2, 384)
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        """
        Initialize and load the embedding model.

        Args:
            model_name: HuggingFace model identifier or local path.
                        Defaults to all-MiniLM-L6-v2.
        """
        self.model_name = model_name
        self._model = None
        self._dimension = None
        self._load_model()

    def _load_model(self):
        """Load the sentence-transformer model from HuggingFace (cached locally)."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            sys.exit(1)

        logger.info(f"Loading embedding model: {self.model_name}")
        try:
            self._model = SentenceTransformer(self.model_name)
            # Probe the output dimension with a dummy encoding
            dummy = self._model.encode(["test"], show_progress_bar=False)
            self._dimension = dummy.shape[1]
            logger.info(f"Embedding model loaded. Output dimension: {self._dimension}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            logger.error("Check your internet connection for the first-time model download.")
            sys.exit(1)

    def encode(self, texts: List[str], show_progress: bool = True) -> np.ndarray:
        """
        Encode a list of text strings into embedding vectors.

        Args:
            texts: List of strings to encode.
            show_progress: Show a tqdm progress bar (default: True).

        Returns:
            NumPy float32 array of shape (len(texts), embedding_dimension).
            Returns empty array if input is empty.
        """
        if not texts:
            logger.warning("encode() called with empty text list.")
            return np.empty((0, self._dimension), dtype=np.float32)

        logger.debug(f"Encoding {len(texts)} text(s) in batches of {ENCODING_BATCH_SIZE}.")

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=ENCODING_BATCH_SIZE,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True  # L2 normalize → cosine similarity = dot product
            )
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            raise

        # Ensure float32 (FAISS requirement)
        embeddings = embeddings.astype(np.float32)
        logger.debug(f"Encoding complete. Shape: {embeddings.shape}")
        return embeddings

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single string into a 1D embedding vector.
        Convenience wrapper around encode().

        Args:
            text: The query or sentence to encode.

        Returns:
            1D NumPy float32 array of shape (embedding_dimension,).
        """
        result = self.encode([text], show_progress=False)
        return result[0]

    def get_dimension(self) -> int:
        """Return the embedding output dimension (e.g., 384 for MiniLM-L6)."""
        return self._dimension
