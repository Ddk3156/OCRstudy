"""
study_materials.py — Study Material Generation Module
------------------------------------------------------
Generates educational content from notes:
  - Multiple Choice Questions (MCQs)
  - Summaries
  - Structured study notes
  - Explanations
"""

import logging
from typing import List, Dict
import ollama

logger = logging.getLogger(__name__)


class StudyMaterialGenerator:
    """Generate various study materials from processed notes"""
    
    def __init__(self, qa_engine, ollama_model='mistral'):
        self.qa_engine = qa_engine
        self.ollama_model = ollama_model
    
    def generate_mcqs(self, topic: str, num_questions: int = 5) -> List[Dict]:
        """Generate multiple choice questions on a topic"""
        # Retrieve relevant chunks
        chunks = self._get_relevant_chunks(topic, top_k=5)
        
        if not chunks:
            return []
        
        context = "\n\n".join([c['text'] for c in chunks])
        
        prompt = f"""Based on the following notes, create {num_questions} multiple choice questions about {topic if topic else 'the content'}.

Notes:
{context}

For each question, provide:
1. The question
2. Four options (A, B, C, D)
3. The correct answer
4. A brief explanation

Format as JSON array with structure:
[{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "..."}}]

Only use information from the notes. If insufficient information, create fewer questions."""
        
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.7}
            )
            
            # Parse JSON response
            import json
            content = response["message"]["content"]
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            mcqs = json.loads(content.strip())
            return mcqs[:num_questions]
        
        except Exception as e:
            logger.error(f"MCQ generation failed: {e}")
            return []
    
    def generate_summary(self, topic: str = "") -> str:
        """Generate a summary of notes"""
        chunks = self._get_relevant_chunks(topic, top_k=10)
        
        if not chunks:
            return "I don't have enough information in the notes to create a summary."
        
        context = "\n\n".join([f"[Page {c['page']}] {c['text']}" for c in chunks])
        
        prompt = f"""Create a comprehensive summary of the following notes{' about ' + topic if topic else ''}.

Notes:
{context}

Instructions:
- Organize information logically with clear sections
- Include key concepts, definitions, and important points
- Use bullet points for clarity
- Only use information from the provided notes
- If information is incomplete, note that

Summary:"""
        
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3}
            )
            
            return response["message"]["content"].strip()
        
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return "Error generating summary."
    
    def generate_notes(self, topic: str = "") -> str:
        """Generate structured study notes"""
        chunks = self._get_relevant_chunks(topic, top_k=10)
        
        if not chunks:
            return "I don't have enough information in the notes."
        
        context = "\n\n".join([f"[Page {c['page']}] {c['text']}" for c in chunks])
        
        prompt = f"""Create structured study notes from the following content{' about ' + topic if topic else ''}.

Content:
{context}

Format the notes with:
- Clear headings and subheadings
- Key concepts highlighted
- Important definitions
- Examples where available
- Formulas or procedures if present

Only use information from the provided content.

Study Notes:"""
        
        try:
            response = ollama.chat(
                model=self.ollama_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3}
            )
            
            return response["message"]["content"].strip()
        
        except Exception as e:
            logger.error(f"Notes generation failed: {e}")
            return "Error generating notes."
    
    def _get_relevant_chunks(self, topic: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant chunks for a topic"""
        if not topic:
            # Get diverse chunks from different pages
            vector_store = self.qa_engine.vector_store
            all_metadata = vector_store._metadata
            
            # Sample chunks from different pages
            pages_seen = set()
            chunks = []
            for meta in all_metadata:
                if meta['page'] not in pages_seen:
                    chunks.append(meta)
                    pages_seen.add(meta['page'])
                if len(chunks) >= top_k:
                    break
            
            return chunks
        else:
            # Use semantic search
            query_embedding = self.qa_engine.embedding_model.encode_single(topic)
            return self.qa_engine.vector_store.search(query_embedding, top_k=top_k)
