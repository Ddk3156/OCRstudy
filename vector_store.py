"""
vector_store.py — FAISS Vector Store Module
--------------------------------------------
Stores chunk embeddings in a local FAISS index for fast approximate
nearest-neighbor search. Also persists chunk metadata (text, page, chunk_id)
to disk alongside the FAISS index.

Storage layout (saved to a directory):
    <index_path>/
        index.faiss       — FAISS binary index
        metadata.json     — chunk text + page numbers

FAISS index type: IndexFlatIP (Inner Product)
  - Since embeddings are L2-normalized, inner product == cosine similarity
  - Exact search (no approximation) — suitable for notes up to ~100K chunks
  - For larger collections, consider IndexIVFFlat or IndexHNSWFlat
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# File names inside the saved index directory
FAISS_INDEX_FILENAME = "index.faiss"
METADATA_FILENAME = "metadata.json"


class VectorStore:
    """
    FAISS-backed vector store with chunk metadata management.

    Supports:
      - Adding embeddings + metadata
      - Top-K similarity search
      - Save/load to disk
    """

    def __init__(self, dimension: int):
        """
        Initialize an empty FAISS index.

        Args:
            dimension: Embedding vector dimension (e.g., 384 for MiniLM-L6).
        """
        self.dimension = dimension
        self._index = None
        self._metadata: List[Dict] = []  # Parallel list to FAISS index rows
        self._initialize_index()

    def _initialize_index(self):
        """Create a new FAISS IndexFlatIP (cosine similarity via inner product)."""
        try:
            import faiss
        except ImportError:
            logger.error("faiss-cpu not installed. Run: pip install faiss-cpu")
            sys.exit(1)

        # IndexFlatIP: exact inner product (= cosine sim for normalized vectors)
        self._index = faiss.IndexFlatIP(self.dimension)
        logger.debug(f"FAISS IndexFlatIP initialized with dimension={self.dimension}")

    def add(self, embeddings: np.ndarray, chunks: List[Dict]):
        """
        Add a batch of embeddings and their corresponding chunk metadata.

        Args:
            embeddings: Float32 NumPy array of shape (N, dimension).
            chunks: List of N chunk dicts:
                        [{"chunk_id": int, "page": int, "text": str}, ...]
        """
        if len(embeddings) != len(chunks):
            raise ValueError(
                f"Mismatch: {len(embeddings)} embeddings vs {len(chunks)} chunks."
            )
        if embeddings.ndim != 2 or embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Expected embeddings of shape (N, {self.dimension}), "
                f"got {embeddings.shape}."
            )

        # Ensure float32 (FAISS requirement)
        embeddings = np.ascontiguousarray(embeddings.astype(np.float32))

        self._index.add(embeddings)
        self._metadata.extend(chunks)

        logger.info(f"Added {len(chunks)} vectors. Total in index: {self._index.ntotal}")

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> List[Dict]:
        """
        Find the top-K most similar chunks to a query embedding.

        Args:
            query_embedding: 1D or 2D float32 array of shape (dimension,) or (1, dimension).
            top_k: Number of nearest neighbors to return.

        Returns:
            List of up to top_k chunk dicts, each augmented with a "score" key:
                [{"chunk_id": .., "page": .., "text": .., "score": float}, ...]
            Sorted by descending similarity score.
            Returns empty list if the index is empty.
        """
        if self._index.ntotal == 0:
            logger.warning("Search called on empty index.")
            return []

        # Reshape to 2D if needed
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = np.ascontiguousarray(query_embedding.astype(np.float32))

        # Clamp top_k to available vectors
        k = min(top_k, self._index.ntotal)

        scores, indices = self._index.search(query_embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                # FAISS returns -1 when fewer results than top_k exist
                continue
            chunk = dict(self._metadata[idx])  # Copy to avoid mutating stored data
            chunk["score"] = float(score)
            results.append(chunk)

        logger.debug(f"Search returned {len(results)} result(s) (top_k={top_k}).")
        return results

    def size(self) -> int:
        """Return the number of vectors currently stored in the index."""
        return self._index.ntotal if self._index else 0

    def save(self, directory: str):
        """
        Persist the FAISS index and metadata to disk.

        Creates the directory if it doesn't exist.

        Args:
            directory: Path to the directory where index files will be saved.
        """
        import faiss

        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        faiss_path = dir_path / FAISS_INDEX_FILENAME
        meta_path = dir_path / METADATA_FILENAME

        # Save FAISS binary index
        faiss.write_index(self._index, str(faiss_path))
        logger.info(f"FAISS index saved to: {faiss_path}")

        # Save metadata as JSON
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"Metadata saved to: {meta_path}")

    def load(self, directory: str):
        """
        Load a previously saved FAISS index and metadata from disk.

        Args:
            directory: Path to the directory created by save().

        Raises:
            FileNotFoundError: If the directory or required files don't exist.
        """
        import faiss

        dir_path = Path(directory)
        faiss_path = dir_path / FAISS_INDEX_FILENAME
        meta_path = dir_path / METADATA_FILENAME

        if not faiss_path.is_file():
            raise FileNotFoundError(f"FAISS index not found at: {faiss_path}")
        if not meta_path.is_file():
            raise FileNotFoundError(f"Metadata file not found at: {meta_path}")

        # Load FAISS index
        self._index = faiss.read_index(str(faiss_path))
        logger.info(f"FAISS index loaded from: {faiss_path} ({self._index.ntotal} vectors)")

        # Load metadata
        with open(meta_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)
        logger.info(f"Metadata loaded: {len(self._metadata)} chunk(s).")

        # Validate alignment
        if self._index.ntotal != len(self._metadata):
            logger.warning(
                f"Mismatch between FAISS index ({self._index.ntotal}) "
                f"and metadata ({len(self._metadata)}). Index may be corrupted."
            )
