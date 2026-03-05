# Handwritten Notes Study Assistant

A comprehensive RAG (Retrieval Augmented Generation) system for handwritten PDF notes with OCR, Q&A, and study material generation.

## Features

### 📄 PDF Processing
- Upload handwritten/scanned notes (PDF format)
- Advanced OCR with preprocessing for better accuracy
- Automatic text cleaning and chunking
- Vector embeddings for semantic search

### 💬 Question Answering
- Ask questions about your notes
- Get answers with source page references
- Hallucination prevention - only answers from notes
- Semantic search for relevant content

### 📝 Study Material Generation
- **MCQs**: Generate multiple choice questions with explanations
- **Summaries**: Create comprehensive summaries
- **Study Notes**: Generate structured study notes
- **Explanations**: Get detailed explanations on topics

### 💾 Export Options
- Export to PDF
- Export to DOCX (Word)
- Download offline chatbot package

### 🤖 Offline Chatbot
- Standalone ZIP package
- Runs locally with `npm install && npm start`
- Pre-built vector index included
- Optional API integration

## Installation

### Prerequisites

1. **Python 3.8+**
2. **Tesseract OCR**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # macOS
   brew install tesseract
   
   # Windows
   # Download from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Poppler** (for PDF to image conversion)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   
   # macOS
   brew install poppler
   
   # Windows
   # Download from: https://github.com/oschwartz10612/poppler-windows/releases
   ```

4. **Ollama** (for LLM)
   ```bash
   # Install from: https://ollama.com/download
   
   # Pull a model
   ollama pull mistral
   ```

### Setup

1. **Clone and navigate to directory**
   ```bash
   cd loop
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the web application**
   ```bash
   python app.py
   ```

4. **Open browser**
   ```
   http://localhost:5000
   ```

## Usage

### Web Interface

1. **Upload PDF**
   - Click "Choose PDF File" or drag and drop
   - Wait for OCR processing (may take a few minutes)
   - Status bar shows processing progress

2. **Ask Questions**
   - Go to Q&A tab
   - Type your question
   - Get answers with page references

3. **Generate Study Materials**
   - **MCQs Tab**: Enter topic (optional) and number of questions
   - **Summary Tab**: Enter topic for focused summary
   - **Notes Tab**: Generate structured study notes

4. **Export Content**
   - Go to Export tab
   - Choose format (PDF/DOCX)
   - Download offline chatbot package

### Command Line (Original)

```bash
# Process a PDF and start Q&A
python main.py --pdf notes.pdf

# Use existing index
python main.py --index notes_index

# Specify model
python main.py --pdf notes.pdf --model llama3

# Save index for reuse
python main.py --pdf notes.pdf --save-index my_notes
```

## Architecture

```
PDF Upload
    ↓
OCR Processing (Tesseract)
    ↓
Text Cleaning & Chunking
    ↓
Embedding Generation (sentence-transformers)
    ↓
Vector Store (FAISS)
    ↓
Question → Semantic Search → LLM (Ollama) → Answer
```

## API Endpoints

- `POST /api/upload` - Upload and process PDF
- `POST /api/ask` - Ask a question
- `POST /api/generate/mcq` - Generate MCQs
- `POST /api/generate/summary` - Generate summary
- `POST /api/generate/notes` - Generate study notes
- `POST /api/export/pdf` - Export to PDF
- `POST /api/export/docx` - Export to DOCX
- `POST /api/chatbot/package` - Download chatbot package
- `GET /api/status` - Get session status

## Configuration

### OCR Settings
Edit `ocr_reader.py`:
- `dpi`: Resolution (default: 300)
- Preprocessing parameters for better accuracy

### Chunking
Edit `chunker.py`:
- `CHUNK_SIZE`: Target chunk size (default: 400 chars)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 80 chars)

### Embedding Model
Edit `embeddings.py`:
- `DEFAULT_MODEL_NAME`: Change embedding model

### LLM Model
Change in web UI or command line:
```bash
python main.py --model llama3
```

## Troubleshooting

### OCR Returns Empty Text
- Check Tesseract installation: `tesseract --version`
- Ensure PDF has actual images (not just blank pages)
- Try increasing DPI in `ocr_reader.py`

### Ollama Connection Failed
- Start Ollama service: `ollama serve`
- Pull model: `ollama pull mistral`
- Check if running: `ollama list`

### Out of Memory
- Reduce `ENCODING_BATCH_SIZE` in `embeddings.py`
- Process fewer pages at once
- Use smaller embedding model

### Slow Processing
- Lower DPI (trade-off: accuracy vs speed)
- Use GPU for embeddings (install `faiss-gpu`)
- Reduce chunk overlap

## Performance Tips

- **First run**: Model downloads may take time
- **Large PDFs**: Processing is CPU-intensive
- **Reuse indexes**: Save and load indexes to skip OCR
- **Batch processing**: Process multiple PDFs offline

## License

MIT License

## Credits

- Tesseract OCR
- FAISS by Facebook Research
- Sentence Transformers
- Ollama
- Flask
