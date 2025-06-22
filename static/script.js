// Global state
let pdfProcessed = false;

// DOM elements
const uploadArea = document.querySelector('.upload-area');
const fileInput = document.getElementById('pdfFile');
const uploadForm = document.getElementById('uploadForm');
const queryForm = document.getElementById('queryForm');
const uploadBtn = document.getElementById('uploadBtn');
const queryBtn = document.getElementById('queryBtn');
const questionInput = document.getElementById('question');

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFileUpload();
    initializeForms();
});

// File upload initialization
function initializeFileUpload() {
    // Drag and drop events
    const dragEvents = ['dragenter', 'dragover', 'dragleave', 'drop'];
    
    dragEvents.forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Drag visual feedback
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Drop handling
    uploadArea.addEventListener('drop', handleDrop, false);
    
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
}

// Form initialization
function initializeForms() {
    uploadForm.addEventListener('submit', handleUploadSubmit);
    queryForm.addEventListener('submit', handleQuerySubmit);
}

// Utility functions
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    uploadArea.classList.add('dragover');
}

function unhighlight() {
    uploadArea.classList.remove('dragover');
}

// File handling
function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelect();
    }
}

function handleFileSelect() {
    const file = fileInput.files[0];
    if (file) {
        const uploadText = document.querySelector('.upload-text');
        uploadText.textContent = `Selected: ${file.name}`;
        uploadText.style.fontWeight = '500';
    }
}

// Form submissions
async function handleUploadSubmit(e) {
    e.preventDefault();
    
    const file = fileInput.files[0];
    
    // Validation
    if (!file) {
        showResult('uploadResult', 'Please select a PDF file', 'error');
        return;
    }
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showResult('uploadResult', 'Please select a valid PDF file', 'error');
        return;
    }
    
    if (file.size > 16 * 1024 * 1024) { // 16MB limit
        showResult('uploadResult', 'File size exceeds 16MB limit', 'error');
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append('pdf', file);
    
    // UI updates
    showLoading('uploadLoading', true);
    hideResult('uploadResult');
    setButtonState(uploadBtn, false);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showResult('uploadResult', result.message, 'success');
            pdfProcessed = true;
            setButtonState(queryBtn, true);
            questionInput.focus();
        } else {
            showResult('uploadResult', result.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showResult('uploadResult', `Error: ${error.message}`, 'error');
    } finally {
        showLoading('uploadLoading', false);
        setButtonState(uploadBtn, true);
    }
}

async function handleQuerySubmit(e) {
    e.preventDefault();
    
    // Validation
    if (!pdfProcessed) {
        showResult('queryResult', 'Please upload and process a PDF first', 'error');
        return;
    }
    
    const question = questionInput.value.trim();
    if (!question) {
        questionInput.focus();
        return;
    }
    
    // UI updates
    showLoading('queryLoading', true);
    clearQueryResult();
    setButtonState(queryBtn, false);
    
    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question: question })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayAnswer(result.answer, result.relevant_docs);
        } else {
            showResult('queryResult', result.error || 'Query failed', 'error');
        }
    } catch (error) {
        console.error('Query error:', error);
        showResult('queryResult', `Error: ${error.message}`, 'error');
    } finally {
        showLoading('queryLoading', false);
        setButtonState(queryBtn, true);
    }
}

// UI utility functions
function showLoading(elementId, show) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = show ? 'block' : 'none';
    }
}

function showResult(elementId, message, type) {
    const element = document.getElementById(elementId);
    if (element) {
        element.className = `result ${type}`;
        element.textContent = message;
        element.style.display = 'block';
    }
}

function hideResult(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function clearQueryResult() {
    const element = document.getElementById('queryResult');
    if (element) {
        element.innerHTML = '';
    }
}

function setButtonState(button, enabled) {
    if (button) {
        button.disabled = !enabled;
    }
}

function displayAnswer(answer, docs) {
    const resultElement = document.getElementById('queryResult');
    if (!resultElement) return;
    
    let html = `
        <div class="answer">
            <h3>Answer</h3>
            <p>${escapeHtml(answer)}</p>
        </div>
    `;
    
    if (docs && docs.length > 0) {
        html += `
            <div class="documents">
                <h3>Relevant Document Excerpts</h3>
        `;
        
        docs.forEach(doc => {
            html += `
                <div class="doc-item">
                    <div class="doc-score">Relevance Score: ${doc.score.toFixed(4)}</div>
                    <div>${escapeHtml(doc.content)}</div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    resultElement.innerHTML = html;
}

// Security utility
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
});