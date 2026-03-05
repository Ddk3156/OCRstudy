"""
app.py — Flask Web Application for Handwritten Notes RAG System
----------------------------------------------------------------
Provides a web UI for:
  - PDF upload and OCR processing
  - Interactive Q&A with source references
  - Study material generation (MCQs, summaries, notes)
  - Document export (PDF, DOCX)
  - Offline chatbot package generation
"""

import os
import json
import logging
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import secrets

from ocr_reader import extract_text_from_pdf
from chunker import clean_and_chunk_text
from embeddings import EmbeddingModel
from vector_store import VectorStore
from qa_engine import QAEngine
from study_materials import StudyMaterialGenerator
from export_utils import export_to_pdf, export_to_docx
from chatbot_packager import create_chatbot_package

app = Flask(__name__)
CORS(app)
app.secret_key = secrets.token_hex(32)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Global state
embedding_model = None
vector_stores = {}  # session_id -> VectorStore
qa_engines = {}     # session_id -> QAEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_session_id():
    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)
    return session['session_id']


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_pdf():
    """Upload and process PDF with OCR"""
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files allowed'}), 400
    
    try:
        session_id = get_session_id()
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{session_id}_{filename}")
        file.save(filepath)
        
        # OCR Processing
        logger.info(f"Starting OCR for {filename}")
        pages = extract_text_from_pdf(filepath)
        
        if not pages:
            return jsonify({'error': 'OCR failed - no text extracted'}), 500
        
        # Chunking
        chunks = clean_and_chunk_text(pages)
        if not chunks:
            return jsonify({'error': 'No valid chunks created'}), 500
        
        # Generate embeddings
        global embedding_model
        if embedding_model is None:
            embedding_model = EmbeddingModel()
        
        texts = [c["text"] for c in chunks]
        embeddings = embedding_model.encode(texts)
        
        # Build vector store
        vector_store = VectorStore(dimension=embeddings.shape[1])
        vector_store.add(embeddings, chunks)
        
        # Save to session
        vector_stores[session_id] = vector_store
        qa_engines[session_id] = QAEngine(
            vector_store=vector_store,
            embedding_model=embedding_model,
            ollama_model='mistral'
        )
        
        session['pdf_name'] = filename
        session['num_pages'] = len(pages)
        session['num_chunks'] = len(chunks)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'pages': len(pages),
            'chunks': len(chunks)
        })
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Answer a question using RAG"""
    session_id = get_session_id()
    
    if session_id not in qa_engines:
        return jsonify({'error': 'No PDF processed yet'}), 400
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'Question cannot be empty'}), 400
    
    try:
        qa_engine = qa_engines[session_id]
        result = qa_engine.answer(question, top_k=3)
        
        return jsonify({
            'answer': result['answer'],
            'sources': result['sources'],
            'chunks': [{'text': c['text'][:200], 'page': c['page']} for c in result['chunks']]
        })
    
    except Exception as e:
        logger.error(f"Q&A error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate/mcq', methods=['POST'])
def generate_mcq():
    """Generate multiple choice questions"""
    session_id = get_session_id()
    
    if session_id not in qa_engines:
        return jsonify({'error': 'No PDF processed yet'}), 400
    
    data = request.get_json()
    topic = data.get('topic', '')
    num_questions = data.get('num_questions', 5)
    
    try:
        generator = StudyMaterialGenerator(qa_engines[session_id])
        mcqs = generator.generate_mcqs(topic, num_questions)
        
        return jsonify({'mcqs': mcqs})
    
    except Exception as e:
        logger.error(f"MCQ generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate/summary', methods=['POST'])
def generate_summary():
    """Generate summary of notes"""
    session_id = get_session_id()
    
    if session_id not in qa_engines:
        return jsonify({'error': 'No PDF processed yet'}), 400
    
    data = request.get_json()
    topic = data.get('topic', '')
    
    try:
        generator = StudyMaterialGenerator(qa_engines[session_id])
        summary = generator.generate_summary(topic)
        
        return jsonify({'summary': summary})
    
    except Exception as e:
        logger.error(f"Summary generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate/notes', methods=['POST'])
def generate_notes():
    """Generate structured study notes"""
    session_id = get_session_id()
    
    if session_id not in qa_engines:
        return jsonify({'error': 'No PDF processed yet'}), 400
    
    data = request.get_json()
    topic = data.get('topic', '')
    
    try:
        generator = StudyMaterialGenerator(qa_engines[session_id])
        notes = generator.generate_notes(topic)
        
        return jsonify({'notes': notes})
    
    except Exception as e:
        logger.error(f"Notes generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/pdf', methods=['POST'])
def export_pdf():
    """Export content to PDF"""
    data = request.get_json()
    content = data.get('content', '')
    title = data.get('title', 'Study Material')
    
    try:
        pdf_path = export_to_pdf(content, title)
        return send_file(pdf_path, as_attachment=True, download_name=f"{title}.pdf")
    
    except Exception as e:
        logger.error(f"PDF export error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/docx', methods=['POST'])
def export_docx():
    """Export content to DOCX"""
    data = request.get_json()
    content = data.get('content', '')
    title = data.get('title', 'Study Material')
    
    try:
        docx_path = export_to_docx(content, title)
        return send_file(docx_path, as_attachment=True, download_name=f"{title}.docx")
    
    except Exception as e:
        logger.error(f"DOCX export error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chatbot/package', methods=['POST'])
def package_chatbot():
    """Create offline chatbot package"""
    session_id = get_session_id()
    
    if session_id not in vector_stores:
        return jsonify({'error': 'No PDF processed yet'}), 400
    
    try:
        vector_store = vector_stores[session_id]
        zip_path = create_chatbot_package(vector_store, session_id)
        
        return send_file(zip_path, as_attachment=True, download_name='chatbot_package.zip')
    
    except Exception as e:
        logger.error(f"Chatbot packaging error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current session status"""
    session_id = get_session_id()
    
    return jsonify({
        'has_pdf': session_id in vector_stores,
        'pdf_name': session.get('pdf_name', ''),
        'num_pages': session.get('num_pages', 0),
        'num_chunks': session.get('num_chunks', 0)
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
