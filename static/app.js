// Global state
let currentContent = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkStatus();
    setupFileUpload();
});

// Check session status
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.has_pdf) {
            updateStatus(`📄 ${data.pdf_name} - ${data.num_pages} pages, ${data.num_chunks} chunks`);
            showMainTabs();
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

// Setup file upload
function setupFileUpload() {
    const input = document.getElementById('pdfInput');
    const uploadArea = document.getElementById('uploadArea');
    
    input.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#667eea';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#ddd';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#ddd';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            handleFileSelect();
        }
    });
}

// Handle file selection
async function handleFileSelect() {
    const input = document.getElementById('pdfInput');
    const file = input.files[0];
    
    if (!file) return;
    
    if (!file.name.endsWith('.pdf')) {
        alert('Please select a PDF file');
        return;
    }
    
    const formData = new FormData();
    formData.append('pdf', file);
    
    showProgress();
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateStatus(`📄 ${data.filename} - ${data.pages} pages, ${data.chunks} chunks`);
            hideProgress();
            showMainTabs();
            showNotification('PDF processed successfully!', 'success');
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        hideProgress();
        showNotification('Error: ' + error.message, 'error');
    }
}

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName + 'Tab').classList.add('active');
}

// Q&A Functions
function handleQuestionKeyPress(event) {
    if (event.key === 'Enter') {
        askQuestion();
    }
}

async function askQuestion() {
    const input = document.getElementById('questionInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    const chatContainer = document.getElementById('chatContainer');
    
    // Add user message
    addChatMessage(question, 'user');
    input.value = '';
    
    showLoading();
    
    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Add bot response
        let botMessage = `<strong>Assistant:</strong> ${data.answer}`;
        
        if (data.sources && data.sources.length > 0) {
            botMessage += `<div class="source-ref">📚 Sources: Page ${data.sources.join(', ')}</div>`;
        }
        
        addChatMessage(botMessage, 'bot');
        
    } catch (error) {
        addChatMessage(`<strong>Error:</strong> ${error.message}`, 'bot');
    } finally {
        hideLoading();
    }
}

function addChatMessage(message, type) {
    const chatContainer = document.getElementById('chatContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}-message`;
    messageDiv.innerHTML = message;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// MCQ Generation
async function generateMCQ() {
    const topic = document.getElementById('mcqTopic').value.trim();
    const count = parseInt(document.getElementById('mcqCount').value);
    const resultsDiv = document.getElementById('mcqResults');
    
    resultsDiv.innerHTML = '<p>Generating MCQs...</p>';
    showLoading();
    
    try {
        const response = await fetch('/api/generate/mcq', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, num_questions: count })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        displayMCQs(data.mcqs);
        currentContent = formatMCQsForExport(data.mcqs);
        
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

function displayMCQs(mcqs) {
    const resultsDiv = document.getElementById('mcqResults');
    
    if (!mcqs || mcqs.length === 0) {
        resultsDiv.innerHTML = '<p>No MCQs generated. Try a different topic.</p>';
        return;
    }
    
    let html = '';
    mcqs.forEach((mcq, index) => {
        html += `
            <div class="mcq-item">
                <div class="mcq-question">${index + 1}. ${mcq.question}</div>
                ${Object.entries(mcq.options).map(([key, value]) => `
                    <div class="mcq-option ${key === mcq.correct ? 'correct' : ''}" 
                         onclick="this.classList.toggle('correct')">
                        ${key}. ${value}
                    </div>
                `).join('')}
                <div class="mcq-explanation">
                    <strong>Answer:</strong> ${mcq.correct}<br>
                    <strong>Explanation:</strong> ${mcq.explanation}
                </div>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}

function formatMCQsForExport(mcqs) {
    let text = '# Multiple Choice Questions\n\n';
    mcqs.forEach((mcq, index) => {
        text += `## Question ${index + 1}\n${mcq.question}\n\n`;
        Object.entries(mcq.options).forEach(([key, value]) => {
            text += `${key}. ${value}\n`;
        });
        text += `\n**Answer:** ${mcq.correct}\n`;
        text += `**Explanation:** ${mcq.explanation}\n\n`;
    });
    return text;
}

// Summary Generation
async function generateSummary() {
    const topic = document.getElementById('summaryTopic').value.trim();
    const resultsDiv = document.getElementById('summaryResults');
    
    resultsDiv.innerHTML = '<p>Generating summary...</p>';
    showLoading();
    
    try {
        const response = await fetch('/api/generate/summary', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        resultsDiv.innerHTML = `<div style="white-space: pre-wrap;">${data.summary}</div>`;
        currentContent = data.summary;
        document.getElementById('exportContent').value = data.summary;
        
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

// Notes Generation
async function generateNotes() {
    const topic = document.getElementById('notesTopic').value.trim();
    const resultsDiv = document.getElementById('notesResults');
    
    resultsDiv.innerHTML = '<p>Generating notes...</p>';
    showLoading();
    
    try {
        const response = await fetch('/api/generate/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        resultsDiv.innerHTML = `<div style="white-space: pre-wrap;">${data.notes}</div>`;
        currentContent = data.notes;
        document.getElementById('exportContent').value = data.notes;
        
    } catch (error) {
        resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    } finally {
        hideLoading();
    }
}

// Export Functions
async function exportToPDF() {
    const content = document.getElementById('exportContent').value || currentContent;
    
    if (!content) {
        alert('No content to export. Generate some content first.');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/export/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, title: 'Study Material' })
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadBlob(blob, 'study_material.pdf');
        showNotification('PDF exported successfully!', 'success');
        
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function exportToDOCX() {
    const content = document.getElementById('exportContent').value || currentContent;
    
    if (!content) {
        alert('No content to export. Generate some content first.');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/export/docx', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content, title: 'Study Material' })
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadBlob(blob, 'study_material.docx');
        showNotification('DOCX exported successfully!', 'success');
        
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function downloadChatbot() {
    showLoading();
    
    try {
        const response = await fetch('/api/chatbot/package', {
            method: 'POST'
        });
        
        if (!response.ok) throw new Error('Package creation failed');
        
        const blob = await response.blob();
        downloadBlob(blob, 'chatbot_package.zip');
        showNotification('Chatbot package downloaded!', 'success');
        
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Utility Functions
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

function updateStatus(text) {
    document.getElementById('statusText').textContent = text;
}

function showProgress() {
    document.getElementById('uploadArea').style.display = 'none';
    document.getElementById('progressContainer').style.display = 'block';
    
    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += 5;
        if (progress >= 90) {
            clearInterval(interval);
        }
        document.getElementById('progressFill').style.width = progress + '%';
    }, 200);
}

function hideProgress() {
    document.getElementById('progressContainer').style.display = 'none';
    document.getElementById('uploadArea').style.display = 'block';
    document.getElementById('progressFill').style.width = '0%';
}

function showMainTabs() {
    document.getElementById('mainTabs').style.display = 'flex';
    document.getElementById('qaTab').style.display = 'block';
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

function showNotification(message, type) {
    // Simple alert for now - can be enhanced with toast notifications
    alert(message);
}
