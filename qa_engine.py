"""
qa_engine.py — RAG Question Answering Engine
---------------------------------------------
Implements the full Retrieval Augmented Generation (RAG) loop:

  1. Embed the user's question
  2. Retrieve the top-K most relevant chunks from the vector store
  3. Build a grounded prompt with retrieved context
  4. Call the local Ollama LLM to generate an answer
  5. Return the answer with source page citations

The LLM is explicitly instructed to answer ONLY from the provided context.
If the answer isn't in the notes, it must say so — no hallucination allowed.
"""

import logging
import sys
from typing import List, Dict, Any

from embeddings import EmbeddingModel
from vector_store import VectorStore

logger = logging.getLogger(__name__)

# ── PROMPT TEMPLATE ───────────────────────────────────────────────────────────
# Strict grounding prompt: the model MUST only use the context.
# We include a hard no-hallucination instruction to minimize confabulation.

PROMPT_TEMPLATE = """You are a helpful assistant that answers questions based ONLY on handwritten notes.

Context from the notes:
{context}

Question: {question}

Instructions:
- Answer ONLY using the information provided in the context above.
- Be concise and accurate.
- If the answer is not present in the context, respond with EXACTLY:
  "I don't have enough information in the notes."
- Do NOT use any outside knowledge or make assumptions.
- Do NOT guess or infer beyond what is explicitly stated.

Answer:"""

# Fallback message (also returned if LLM call fails)
NO_INFO_RESPONSE = "I don't have enough information in the notes."

# Minimum similarity score threshold — chunks below this are likely irrelevant
MIN_RELEVANCE_SCORE = 0.20


class QAEngine:
    """
    RAG Question Answering engine.

    Combines:
      - Semantic retrieval via VectorStore
      - Answer generation via Ollama (local LLM)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: EmbeddingModel,
        ollama_model: str = "mistral"
    ):
        """
        Initialize the QA engine.

        Args:
            vector_store: Populated VectorStore instance.
            embedding_model: Loaded EmbeddingModel instance.
            ollama_model: Name of the Ollama model to use (e.g., "mistral", "llama3").
        """
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.ollama_model = ollama_model
        self._check_ollama()

    def _check_ollama(self):
        """
        Verify that Ollama is installed and the requested model is available.
        Logs a warning (not a fatal error) so the system can still retrieve
        chunks even if generation is unavailable.
        """
        try:
            import ollama
            available_models = [m.model for m in ollama.list().models]
            logger.debug(f"Ollama models available: {available_models}")
            if self.ollama_model not in available_models:
                logger.warning(
                    f"Ollama model '{self.ollama_model}' not found locally. "
                    f"Pull it with: ollama pull {self.ollama_model}\n"
                    f"Available: {available_models}"
                )
                print(f"\n⚠️  Warning: Ollama model '{self.ollama_model}' not found.")
                print(f"   Run: ollama pull {self.ollama_model}")
                print("   The system will attempt to use it anyway.\n")
        except ImportError:
            logger.error("ollama Python package not installed. Run: pip install ollama")
            sys.exit(1)
        except Exception as e:
            logger.warning(f"Could not connect to Ollama service: {e}")
            print(f"\n⚠️  Warning: Cannot connect to Ollama ({e})")
            print("   Make sure Ollama is running: https://ollama.com/download\n")

    def _retrieve_chunks(self, question: str, top_k: int) -> List[Dict]:
        """
        Embed the question and retrieve the top-K relevant chunks.

        Applies a relevance threshold to filter out chunks that are
        semantically distant (likely unrelated to the question).

        Args:
            question: The user's question string.
            top_k: Maximum number of chunks to retrieve.

        Returns:
            List of relevant chunk dicts with "score" field, sorted by score.
            May return fewer than top_k if low-scoring chunks are filtered.
        """
        query_embedding = self.embedding_model.encode_single(question)
        results = self.vector_store.search(query_embedding, top_k=top_k)

        # Filter out low-relevance chunks
        relevant = [r for r in results if r["score"] >= MIN_RELEVANCE_SCORE]

        if not relevant and results:
            logger.info(
                f"All chunks scored below threshold ({MIN_RELEVANCE_SCORE}). "
                f"Best score was {results[0]['score']:.3f}. Returning top result anyway."
            )
            # Return at least the best match — let the LLM decide if it's useful
            relevant = [results[0]]

        logger.debug(
            f"Retrieved {len(relevant)} chunk(s) for question. "
            f"Scores: {[round(r['score'], 3) for r in relevant]}"
        )
        return relevant

    def _build_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into a readable context block for the prompt.

        Each chunk is prefixed with its source page number.

        Args:
            chunks: List of chunk dicts from vector store search.

        Returns:
            Formatted context string.
        """
        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            part = f"[Excerpt {i} — Page {chunk['page']}]\n{chunk['text']}"
            context_parts.append(part)
        return "\n\n".join(context_parts)

    def _call_ollama(self, prompt: str) -> str:
        """
        Send a prompt to the local Ollama LLM and return the response text.

        Uses a low temperature (0.1) to minimize creativity/hallucination.

        Args:
            prompt: The complete formatted prompt string.

        Returns:
            The model's response text.
            Falls back to NO_INFO_RESPONSE on any error.
        """
        try:
            import ollama

            logger.debug(f"Sending prompt to Ollama model '{self.ollama_model}'...")
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                options={
                    "temperature": 0.1,       # Low temp = more factual, less creative
                    "top_p": 0.9,
                    "num_predict": 512,       # Max tokens in response
                    "stop": ["\n\nQuestion:", "\n\nContext:"]  # Prevent runaway generation
                }
            )
            answer = response["message"]["content"].strip()
            logger.debug(f"Ollama response length: {len(answer)} chars.")
            return answer

        except Exception as e:
            logger.error(f"Ollama call failed: {e}")
            print(f"\n❌ Error calling Ollama: {e}")
            print("   Make sure Ollama is running and the model is downloaded.")
            return NO_INFO_RESPONSE

    def answer(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Full RAG pipeline: question → retrieve → generate → return.

        Args:
            question: The user's natural language question.
            top_k: Number of chunks to retrieve from the vector store.

        Returns:
            Dict with keys:
                "answer"  (str): The generated answer or fallback message.
                "sources" (list[int]): Page numbers of retrieved source chunks.
                "chunks"  (list[dict]): Full retrieved chunk data (for debugging).
        """
        logger.info(f"Processing question: '{question[:80]}...'")

        # Step 1: Retrieve relevant chunks
        relevant_chunks = self._retrieve_chunks(question, top_k=top_k)

        if not relevant_chunks:
            logger.info("No relevant chunks found — returning no-info response.")
            return {
                "answer": NO_INFO_RESPONSE,
                "sources": [],
                "chunks": []
            }

        # Step 2: Build context from retrieved chunks
        context = self._build_context(relevant_chunks)

        # Step 3: Format the grounded prompt
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)
        logger.debug(f"Prompt length: {len(prompt)} chars.")

        # Step 4: Generate answer via local LLM
        raw_answer = self._call_ollama(prompt)

        # Step 5: Post-process — check if LLM signaled lack of information
        # (Some models rephrase the fallback message; normalize it)
        answer = self._normalize_answer(raw_answer)

        # Collect unique source pages
        source_pages = list({chunk["page"] for chunk in relevant_chunks})

        return {
            "answer": answer,
            "sources": source_pages,
            "chunks": relevant_chunks
        }

    def _normalize_answer(self, raw_answer: str) -> str:
        """
        Normalize the LLM's answer.

        If the model signals it doesn't have information (in various phrasings),
        return the canonical NO_INFO_RESPONSE string for consistency.

        Args:
            raw_answer: Raw text from the LLM.

        Returns:
            Normalized answer string.
        """
        if not raw_answer or not raw_answer.strip():
            return NO_INFO_RESPONSE

        answer_lower = raw_answer.lower()

        # Common LLM phrasings for "I don't know"
        no_info_signals = [
            "i don't have enough information",
            "i do not have enough information",
            "not present in the context",
            "not mentioned in the notes",
            "cannot find this information",
            "not found in the provided context",
            "not in the context",
            "the context does not",
            "the notes do not contain",
        ]

        for signal in no_info_signals:
            if signal in answer_lower:
                return NO_INFO_RESPONSE

        return raw_answer.strip()
