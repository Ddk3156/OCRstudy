# Project Structure

```
loop/
├── app.py                      # Flask web application (main entry point)
├── main.py                     # CLI version (original)
├── requirements.txt            # Python dependencies
│
├── Core Modules
│   ├── ocr_reader.py          # PDF OCR extraction with preprocessing
│   ├── chunker.py             # Text cleaning and chunking
│   ├── embeddings.py          # Sentence transformer embeddings
│   ├── vector_store.py        # FAISS vector database
│   ├── qa_engine.py           # RAG question answering
│   ├── study_materials.py     # MCQ, summary, notes generation
│   ├── export_utils.py        # PDF/DOCX export functionality
│   ├── chatbot_packager.py    # Offline chatbot package creator
│   └── utils.py               # Utility functions
│
├── Web Interface
│   ├── templates/
│   │   └── index.html         # Main web UI
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css      # Styling
│   │   └── js/
│   │       └── app.js         # Frontend JavaScript
│   └── uploads/               # Temporary PDF storage (created at runtime)
│
├── Documentation
│   ├── README.md              # Full documentation
│   ├── QUICKSTART.md          # Quick start guide
│   └── PROJECT_STRUCTURE.md   # This file
│
├── Scripts
│   ├── start.sh               # Linux/macOS startup script
│   ├── start.bat              # Windows startup script
│   └── test_system.py         # System test script
│
└── Configuration
    └── .env.example           # Environment variables template
```

## Module Descriptions

### Core Processing Pipeline

#### 1. ocr_reader.py
- Converts PDF pages to images
- Applies preprocessing (grayscale, denoising, deskewing)
- Runs Tesseract OCR
- Returns structured page data

**Key Functions:**
- `extract_text_from_pdf(pdf_path, dpi=300)` → List[Dict]
- `_preprocess_image_for_ocr(pil_image, cv2)` → PIL.Image
- `_deskew(binary_image, cv2)` → np.ndarray

#### 2. chunker.py
- Cleans OCR artifacts and noise
- Splits text into semantic chunks
- Adds metadata (page numbers, chunk IDs)

**Key Functions:**
- `clean_and_chunk_text(pages)` → List[Dict]
- `clean_ocr_text(raw_text)` → str
- `_build_chunks_with_overlap(sentences, page, chunk_id_start)` → List[Dict]

#### 3. embeddings.py
- Loads sentence-transformers model
- Generates dense vector embeddings
- Normalizes vectors for cosine similarity

**Key Functions:**
- `EmbeddingModel.encode(texts)` → np.ndarray
- `EmbeddingModel.encode_single(text)` → np.ndarray
- `EmbeddingModel.get_dimension()` → int

#### 4. vector_store.py
- FAISS index management
- Semantic similarity search
- Save/load functionality

**Key Functions:**
- `VectorStore.add(embeddings, chunks)` → None
- `VectorStore.search(query_embedding, top_k)` → List[Dict]
- `VectorStore.save(directory)` / `load(directory)` → None

#### 5. qa_engine.py
- RAG implementation
- Retrieves relevant chunks
- Generates answers via Ollama
- Prevents hallucination

**Key Functions:**
- `QAEngine.answer(question, top_k)` → Dict
- `_retrieve_chunks(question, top_k)` → List[Dict]
- `_call_ollama(prompt)` → str

#### 6. study_materials.py
- Generates MCQs with explanations
- Creates summaries
- Produces structured study notes

**Key Functions:**
- `StudyMaterialGenerator.generate_mcqs(topic, num_questions)` → List[Dict]
- `StudyMaterialGenerator.generate_summary(topic)` → str
- `StudyMaterialGenerator.generate_notes(topic)` → str

#### 7. export_utils.py
- Exports content to PDF (reportlab)
- Exports content to DOCX (python-docx)
- Handles formatting and styling

**Key Functions:**
- `export_to_pdf(content, title)` → str (file path)
- `export_to_docx(content, title)` → str (file path)

#### 8. chatbot_packager.py
- Creates standalone chatbot package
- Includes Node.js server
- Bundles vector index
- Generates setup instructions

**Key Functions:**
- `create_chatbot_package(vector_store, session_id)` → str (zip path)

### Web Application

#### app.py
Flask application with REST API endpoints:

**Endpoints:**
- `POST /api/upload` - Upload and process PDF
- `POST /api/ask` - Ask questions
- `POST /api/generate/mcq` - Generate MCQs
- `POST /api/generate/summary` - Generate summary
- `POST /api/generate/notes` - Generate notes
- `POST /api/export/pdf` - Export to PDF
- `POST /api/export/docx` - Export to DOCX
- `POST /api/chatbot/package` - Download chatbot
- `GET /api/status` - Session status

**Session Management:**
- Uses Flask sessions
- Stores vector stores per session
- Maintains QA engines per user

#### templates/index.html
Single-page application with tabs:
- Upload section
- Q&A interface
- MCQ generator
- Summary generator
- Notes generator
- Export options

#### static/css/style.css
Modern, responsive design:
- Gradient backgrounds
- Card-based layout
- Smooth animations
- Mobile-friendly

#### static/js/app.js
Frontend logic:
- File upload with drag-and-drop
- AJAX API calls
- Dynamic content rendering
- Tab switching
- Progress indicators

## Data Flow

### Upload & Processing
```
User uploads PDF
    ↓
app.py receives file
    ↓
ocr_reader.py extracts text
    ↓
chunker.py cleans and chunks
    ↓
embeddings.py generates vectors
    ↓
vector_store.py indexes chunks
    ↓
Session stores vector_store & qa_engine
```

### Question Answering
```
User asks question
    ↓
app.py /api/ask endpoint
    ↓
qa_engine.answer()
    ↓
embeddings.py encodes question
    ↓
vector_store.py searches similar chunks
    ↓
qa_engine calls Ollama with context
    ↓
Returns answer + sources
```

### Study Material Generation
```
User requests MCQs/summary/notes
    ↓
app.py /api/generate/* endpoint
    ↓
study_materials.py retrieves chunks
    ↓
Ollama generates content
    ↓
Returns formatted material
```

### Export
```
User clicks export
    ↓
app.py /api/export/* endpoint
    ↓
export_utils.py creates document
    ↓
Returns file for download
```

## Configuration

### Environment Variables (.env)
- Flask settings (host, port, debug)
- Upload limits
- OCR parameters
- Model names
- Chunking settings

### Runtime Configuration
- Modify module constants for fine-tuning
- Adjust prompts in qa_engine.py and study_materials.py
- Change UI styling in style.css

## Dependencies

### System Requirements
- Python 3.8+
- Tesseract OCR
- Poppler (PDF tools)
- Ollama (LLM)

### Python Packages
- **OCR**: pdf2image, pytesseract, Pillow, opencv-python
- **ML**: faiss-cpu, sentence-transformers, numpy
- **LLM**: ollama
- **Web**: Flask, Flask-CORS
- **Export**: reportlab, python-docx

## Extending the System

### Add New Study Material Type
1. Add method to `study_materials.py`
2. Create API endpoint in `app.py`
3. Add UI tab in `index.html`
4. Add handler in `app.js`

### Change Embedding Model
1. Update `DEFAULT_MODEL_NAME` in `embeddings.py`
2. Adjust `dimension` in vector store initialization

### Add New Export Format
1. Add export function to `export_utils.py`
2. Create API endpoint in `app.py`
3. Add button in export tab

### Customize Prompts
- Edit `PROMPT_TEMPLATE` in `qa_engine.py`
- Modify prompts in `study_materials.py` methods

## Performance Optimization

### Speed Improvements
- Use GPU: Install `faiss-gpu` instead of `faiss-cpu`
- Reduce DPI: Lower OCR resolution (trade-off: accuracy)
- Batch processing: Process multiple PDFs offline
- Cache indexes: Save and reuse vector stores

### Memory Optimization
- Reduce `ENCODING_BATCH_SIZE` in `embeddings.py`
- Lower `CHUNK_SIZE` in `chunker.py`
- Process smaller PDFs
- Use smaller embedding model

## Security Considerations

- File upload validation (PDF only, size limits)
- Session-based isolation
- Temporary file cleanup
- No persistent storage of user data
- Local processing (no external API calls except Ollama)

## Testing

Run system test:
```bash
python test_system.py
```

Tests:
- Python version
- Tesseract installation
- Poppler installation
- Ollama availability
- Python packages
- Embedding model download

## Deployment

### Local Development
```bash
python app.py
```

### Production
- Use production WSGI server (gunicorn, uWSGI)
- Set `FLASK_ENV=production`
- Configure proper logging
- Set up reverse proxy (nginx)
- Enable HTTPS

### Docker (Future)
- Create Dockerfile
- Include all dependencies
- Pre-download models
- Volume mount for uploads

## Troubleshooting

See README.md and QUICKSTART.md for common issues and solutions.
