#!/bin/bash

echo "🚀 Starting Handwritten Notes Study Assistant"
echo "=============================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract not found. Please install Tesseract OCR"
    echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "   macOS: brew install tesseract"
    exit 1
fi

# Check Ollama
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama not found. Please install from https://ollama.com/download"
    echo "   Continuing anyway..."
else
    echo "✅ Ollama found"
    
    # Check if mistral model is available
    if ! ollama list | grep -q "mistral"; then
        echo "⚠️  Mistral model not found. Pulling now..."
        ollama pull mistral
    fi
fi

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting web server on http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

python app.py
