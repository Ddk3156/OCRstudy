"""
chatbot_packager.py — Offline Chatbot Package Generator
--------------------------------------------------------
Creates a standalone ZIP package containing:
  - Pre-built vector index
  - Simple Node.js chatbot server
  - HTML/JS frontend
  - Setup instructions
"""

import os
import json
import tempfile
import zipfile
from pathlib import Path


def create_chatbot_package(vector_store, session_id: str) -> str:
    """Create a ZIP package with offline chatbot"""
    
    temp_dir = tempfile.mkdtemp()
    package_dir = os.path.join(temp_dir, 'chatbot')
    os.makedirs(package_dir, exist_ok=True)
    
    # Save vector store
    index_dir = os.path.join(package_dir, 'index')
    vector_store.save(index_dir)
    
    # Create package.json
    package_json = {
        "name": "notes-chatbot",
        "version": "1.0.0",
        "description": "Offline chatbot for handwritten notes",
        "main": "server.js",
        "scripts": {
            "start": "node server.js"
        },
        "dependencies": {
            "express": "^4.18.2",
            "cors": "^2.8.5"
        }
    }
    
    with open(os.path.join(package_dir, 'package.json'), 'w') as f:
        json.dump(package_json, f, indent=2)
    
    # Create server.js
    server_js = """const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

const PORT = process.env.PORT || 3000;

// Simple in-memory search (replace with actual vector search in production)
app.post('/api/ask', (req, res) => {
    const { question } = req.body;
    
    // This is a placeholder - integrate with Python backend or implement JS vector search
    res.json({
        answer: "This is a demo response. Integrate with your Python backend for actual RAG functionality.",
        sources: [1, 2],
        note: "Run the Python backend separately and configure the API endpoint."
    });
});

app.listen(PORT, () => {
    console.log(`Chatbot server running on http://localhost:${PORT}`);
});
"""
    
    with open(os.path.join(package_dir, 'server.js'), 'w') as f:
        f.write(server_js)
    
    # Create public directory
    public_dir = os.path.join(package_dir, 'public')
    os.makedirs(public_dir, exist_ok=True)
    
    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes Chatbot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
        .chat-box { background: white; border-radius: 10px; padding: 20px; min-height: 400px; max-height: 500px; overflow-y: auto; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .message { margin-bottom: 15px; padding: 10px; border-radius: 8px; }
        .user-message { background: #3498db; color: white; margin-left: 20%; }
        .bot-message { background: #ecf0f1; margin-right: 20%; }
        .input-area { display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
        .input-area button { padding: 12px 30px; background: #2c3e50; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
        .input-area button:hover { background: #34495e; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Notes Chatbot</h1>
            <p>Ask questions about your handwritten notes</p>
        </div>
        
        <div class="chat-box" id="chatBox">
            <div class="message bot-message">
                Hello! I'm ready to answer questions about your notes. What would you like to know?
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="questionInput" placeholder="Ask a question..." onkeypress="handleKeyPress(event)">
            <button onclick="askQuestion()">Send</button>
        </div>
    </div>
    
    <script>
        function handleKeyPress(event) {
            if (event.key === 'Enter') askQuestion();
        }
        
        async function askQuestion() {
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            if (!question) return;
            
            const chatBox = document.getElementById('chatBox');
            
            // Add user message
            chatBox.innerHTML += `<div class="message user-message">${question}</div>`;
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question })
                });
                
                const data = await response.json();
                
                // Add bot response
                let botMessage = data.answer;
                if (data.sources && data.sources.length > 0) {
                    botMessage += `<br><br><small>📚 Sources: Page ${data.sources.join(', ')}</small>`;
                }
                
                chatBox.innerHTML += `<div class="message bot-message">${botMessage}</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;
            } catch (error) {
                chatBox.innerHTML += `<div class="message bot-message">Error: ${error.message}</div>`;
            }
        }
    </script>
</body>
</html>"""
    
    with open(os.path.join(public_dir, 'index.html'), 'w') as f:
        f.write(index_html)
    
    # Create README
    readme = """# Notes Chatbot - Offline Package

## Setup Instructions

1. Install Node.js (if not already installed): https://nodejs.org/

2. Install dependencies:
   ```
   npm install
   ```

3. Start the server:
   ```
   npm start
   ```

4. Open your browser to: http://localhost:3000

## Integration with Python Backend

For full RAG functionality, you need to run the Python backend separately:

1. Keep your Python environment active
2. The vector index is included in the `index/` folder
3. Configure the API endpoint in server.js to point to your Python backend

## API Integration

To integrate into your website/app, use the REST API:

```javascript
fetch('http://localhost:3000/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: 'Your question here' })
})
.then(res => res.json())
.then(data => console.log(data.answer));
```

## Files Included

- `server.js` - Express server
- `public/index.html` - Web interface
- `index/` - Pre-built vector index
- `package.json` - Node.js dependencies

## Notes

- This is a standalone package that can run offline
- The vector index is pre-built from your uploaded PDF
- For production use, implement proper vector search in Node.js or connect to Python backend
"""
    
    with open(os.path.join(package_dir, 'README.md'), 'w') as f:
        f.write(readme)
    
    # Create ZIP
    zip_path = os.path.join(temp_dir, f'chatbot_{session_id}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    return zip_path
