#!/usr/bin/env python3
"""
test_system.py — System Test Script
------------------------------------
Verifies all dependencies and components are working correctly
"""

import sys
import subprocess

def test_python():
    """Test Python version"""
    print("🐍 Testing Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need 3.8+)")
        return False

def test_tesseract():
    """Test Tesseract OCR"""
    print("📄 Testing Tesseract OCR...")
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        version = result.stdout.split('\n')[0]
        print(f"   ✅ {version}")
        return True
    except FileNotFoundError:
        print("   ❌ Tesseract not found")
        print("      Install: sudo apt-get install tesseract-ocr")
        return False

def test_poppler():
    """Test Poppler (PDF tools)"""
    print("📑 Testing Poppler...")
    try:
        result = subprocess.run(['pdfinfo', '-v'], 
                              capture_output=True, text=True)
        print("   ✅ Poppler installed")
        return True
    except FileNotFoundError:
        print("   ❌ Poppler not found")
        print("      Install: sudo apt-get install poppler-utils")
        return False

def test_ollama():
    """Test Ollama"""
    print("🤖 Testing Ollama...")
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True)
        if 'mistral' in result.stdout:
            print("   ✅ Ollama with mistral model")
            return True
        else:
            print("   ⚠️  Ollama found but mistral model missing")
            print("      Run: ollama pull mistral")
            return False
    except FileNotFoundError:
        print("   ❌ Ollama not found")
        print("      Install: https://ollama.com/download")
        return False

def test_python_packages():
    """Test Python packages"""
    print("📦 Testing Python packages...")
    
    packages = [
        ('pdf2image', 'pdf2image'),
        ('pytesseract', 'pytesseract'),
        ('PIL', 'Pillow'),
        ('cv2', 'opencv-python'),
        ('faiss', 'faiss-cpu'),
        ('sentence_transformers', 'sentence-transformers'),
        ('numpy', 'numpy'),
        ('ollama', 'ollama'),
        ('flask', 'Flask'),
        ('reportlab', 'reportlab'),
        ('docx', 'python-docx'),
    ]
    
    all_ok = True
    for module, package in packages:
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} not installed")
            all_ok = False
    
    if not all_ok:
        print("\n   Install missing packages:")
        print("   pip install -r requirements.txt")
    
    return all_ok

def test_embedding_model():
    """Test embedding model download"""
    print("🔢 Testing embedding model...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        test_embedding = model.encode(["test"])
        print(f"   ✅ Embedding model loaded (dim: {test_embedding.shape[1]})")
        return True
    except Exception as e:
        print(f"   ❌ Embedding model failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 System Test - Handwritten Notes Study Assistant")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("Python", test_python()))
    results.append(("Tesseract", test_tesseract()))
    results.append(("Poppler", test_poppler()))
    results.append(("Ollama", test_ollama()))
    results.append(("Python Packages", test_python_packages()))
    results.append(("Embedding Model", test_embedding_model()))
    
    print()
    print("=" * 60)
    print("📊 Test Results")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print()
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("🎉 All tests passed! System is ready.")
        print("\nRun the application:")
        print("   python app.py")
        print("\nOr use the start script:")
        print("   ./start.sh")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
