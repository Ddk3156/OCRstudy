@echo off
echo Starting Handwritten Notes Study Assistant
echo ===========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Tesseract
tesseract --version >nul 2>&1
if errorlevel 1 (
    echo Tesseract not found. Please install Tesseract OCR
    echo Download from: https://github.com/UB-Mannheim/tesseract/wiki
    pause
    exit /b 1
)

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo Ollama not found. Please install from https://ollama.com/download
    echo Continuing anyway...
) else (
    echo Ollama found
    
    REM Check if mistral model is available
    ollama list | findstr "mistral" >nul
    if errorlevel 1 (
        echo Mistral model not found. Pulling now...
        ollama pull mistral
    )
)

REM Create virtual environment if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo Setup complete!
echo.
echo Starting web server on http://localhost:5000
echo Press Ctrl+C to stop
echo.

python app.py
