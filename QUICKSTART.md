# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Prerequisites

#### Tesseract OCR
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Windows
# Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
# Download Poppler: https://github.com/oschwartz10612/poppler-windows/releases
```

#### Ollama (Local LLM)
```bash
# Install from: https://ollama.com/download

# After installation, pull a model:
ollama pull mistral
```

### Step 2: Install Python Dependencies

```bash
cd loop
pip install -r requirements.txt
```

### Step 3: Run the Application

#### Option A: Using Start Script (Recommended)
```bash
# Linux/macOS
./start.sh

# Windows
start.bat
```

#### Option B: Direct Python
```bash
python app.py
```

### Step 4: Open Browser

Navigate to: **http://localhost:5000**

## 📖 How to Use

### 1. Upload Your PDF
- Click "Choose PDF File" or drag & drop
- Wait for OCR processing (1-5 minutes depending on size)
- Status bar shows: "📄 filename.pdf - X pages, Y chunks"

### 2. Ask Questions
- Go to **Q&A** tab
- Type: "What is the main topic?"
- Get answers with page references

### 3. Generate Study Materials

#### MCQs
- Go to **MCQs** tab
- Enter topic (optional): "photosynthesis"
- Choose number of questions: 5
- Click "Generate MCQs"

#### Summary
- Go to **Summary** tab
- Enter topic (optional) or leave empty for full summary
- Click "Generate Summary"

#### Study Notes
- Go to **Notes** tab
- Enter topic (optional)
- Click "Generate Notes"

### 4. Export Your Work

#### Export to PDF/DOCX
- Go to **Export** tab
- Generated content appears in text area
- Click "Export PDF" or "Export DOCX"

#### Download Offline Chatbot
- Go to **Export** tab
- Click "Download Package"
- Extract ZIP file
- Run: `npm install && npm start`
- Open: http://localhost:3000

## 🎯 Example Workflow

```
1. Upload: "biology_notes.pdf"
   ↓
2. Ask: "What are the stages of mitosis?"
   → Answer: "The stages are prophase, metaphase..."
   → Sources: Page 12, 13
   ↓
3. Generate: 5 MCQs on "cell division"
   → Get practice questions with explanations
   ↓
4. Generate: Summary of "cell cycle"
   → Get comprehensive summary
   ↓
5. Export: Download as PDF for studying
```

## ⚡ Tips

- **First run**: Model downloads take 5-10 minutes
- **Better OCR**: Use high-quality scans (300 DPI)
- **Faster processing**: Use smaller PDFs (<50 pages)
- **Reuse index**: Save processing time on repeated use
- **Clear handwriting**: Works best with legible notes

## 🔧 Troubleshooting

### "OCR returned no text"
- Check if PDF contains actual images
- Verify Tesseract installation: `tesseract --version`
- Try increasing DPI in settings

### "Cannot connect to Ollama"
- Start Ollama: `ollama serve`
- Check if model exists: `ollama list`
- Pull model: `ollama pull mistral`

### "Out of memory"
- Process smaller PDFs
- Close other applications
- Reduce batch size in settings

### "Slow processing"
- Normal for first run (model downloads)
- Large PDFs take longer
- Consider using GPU version

## 📚 Next Steps

- Read full [README.md](README.md) for advanced features
- Check [API documentation](#api-endpoints) for integration
- Customize settings in configuration files
- Try different LLM models (llama3, phi, etc.)

## 🆘 Need Help?

- Check logs in terminal for error messages
- Verify all prerequisites are installed
- Ensure PDF is not corrupted or password-protected
- Try with a simple test PDF first

## 🎓 Best Practices

1. **Scan Quality**: Use 300 DPI for handwritten notes
2. **File Size**: Keep PDFs under 50 pages for best performance
3. **Handwriting**: Clear, legible writing works best
4. **Topics**: Be specific in questions for better answers
5. **Export**: Save your work regularly

---

**Ready to start?** Run `./start.sh` and open http://localhost:5000 🚀
