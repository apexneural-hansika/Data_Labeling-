/**
 * Frontend JavaScript for AgenticAI data labeling platform
 * Handles file uploads, progress tracking, and result display
 */

// Global state
let currentTaskId = null;
let progressInterval = null;

// DOM elements
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const filePreview = document.getElementById('filePreview');
const fileName = document.getElementById('fileName');
const fileInfo = document.getElementById('fileInfo');
const submitBtn = document.getElementById('submitBtn');
const processingStatus = document.getElementById('processingStatus');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
});

function initializeEventListeners() {
    // File input change
    fileInput.addEventListener('change', handleFileSelect);
    
    // Form submission
    uploadForm.addEventListener('submit', handleFormSubmit);
    
    // Drag and drop
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);
    dropZone.addEventListener('click', () => fileInput.click());
    
    // Expand/collapse sections
    const expandLabels = document.getElementById('expandLabels');
    const expandJson = document.getElementById('expandJson');
    const labelsHeader = document.getElementById('labelsHeader');
    const jsonHeader = document.getElementById('jsonHeader');
    
    if (expandLabels) {
        labelsHeader?.addEventListener('click', () => toggleSection('labels'));
        expandLabels.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSection('labels');
        });
    }
    
    if (expandJson) {
        jsonHeader?.addEventListener('click', () => toggleSection('json'));
        expandJson.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleSection('json');
        });
    }
    
    // Copy JSON button
    const copyBtn = document.getElementById('copyBtn');
    if (copyBtn) {
        copyBtn.addEventListener('click', copyJSONToClipboard);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        displayFileInfo(file);
    }
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    dropZone.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        fileInput.files = files;
        displayFileInfo(files[0]);
    }
}

function displayFileInfo(file) {
    fileName.textContent = file.name;
    fileInfo.innerHTML = `
        <div class="file-details">
            <span>Size: ${formatFileSize(file.size)}</span>
            <span>Type: ${file.type || 'Unknown'}</span>
        </div>
    `;
    filePreview.innerHTML = `
        <div class="file-preview-item">
            <span class="file-icon">${getFileIcon(file.name)}</span>
            <span class="file-name">${file.name}</span>
        </div>
    `;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📄', 'txt': '📝', 'docx': '📘', 'doc': '📘',
        'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
        'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'm4a': '🎵',
        'mp4': '🎬', 'avi': '🎬', 'mov': '🎬'
    };
    return icons[ext] || '📎';
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const file = fileInput.files[0];
    if (!file) {
        showError('Please select a file to upload');
        return;
    }
    
    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File size exceeds 100MB limit');
        return;
    }
    
    // Reset UI
    hideError();
    hideResults();
    showProcessing();
    
    // Disable form
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').textContent = 'Processing...';
    
    try {
        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        // Check if it's an async task
        if (result.task_id) {
            currentTaskId = result.task_id;
            startProgressPolling(result.task_id);
        } else {
            // Synchronous result
            displayResults(result);
            hideProcessing();
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        showError(error.message || 'Failed to process file');
        hideProcessing();
    } finally {
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').textContent = 'Process File';
    }
}

function startProgressPolling(taskId) {
    if (progressInterval) {
        clearInterval(progressInterval);
    }
    
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/task/${taskId}`);
            if (!response.ok) {
                throw new Error('Failed to get task status');
            }
            
            const task = await response.json();
            updateProgress(task);
            
            if (task.status === 'completed') {
                clearInterval(progressInterval);
                progressInterval = null;
                displayResults(task.result);
                hideProcessing();
            } else if (task.status === 'failed') {
                clearInterval(progressInterval);
                progressInterval = null;
                showError(task.error || 'Processing failed');
                hideProcessing();
            }
        } catch (error) {
            console.error('Progress polling error:', error);
        }
    }, 2000); // Poll every 2 seconds
}

function updateProgress(task) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill && progressText) {
        const progress = task.progress || 0;
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}%`;
    }
    
    // Update step statuses
    if (task.current_step) {
        updateStepStatus(task.current_step, 'active');
    }
    
    if (task.completed_steps) {
        task.completed_steps.forEach(step => {
            updateStepStatus(step, 'completed');
        });
    }
}

function updateStepStatus(stepName, status) {
    const step = document.querySelector(`[data-step="${stepName}"]`);
    if (step) {
        const statusIndicator = step.querySelector('.step-status');
        if (statusIndicator) {
            statusIndicator.className = `step-status ${status}`;
        }
    }
}

function displayResults(result) {
    // Update result cards
    const resultFileName = document.getElementById('resultFileName');
    const resultModality = document.getElementById('resultModality');
    const resultCategory = document.getElementById('resultCategory');
    const resultQuality = document.getElementById('resultQuality');
    const qualityBar = document.getElementById('qualityBar');
    const qualityText = document.getElementById('qualityText');
    const labelsGrid = document.getElementById('labelsGrid');
    const resultLabels = document.getElementById('resultLabels');
    const resultFullJson = document.getElementById('resultFullJson');
    
    if (resultFileName) resultFileName.textContent = result.file_name || '-';
    if (resultModality) resultModality.textContent = result.modality || '-';
    if (resultCategory) resultCategory.textContent = result.category || '-';
    
    // Quality score
    const qualityScore = result.quality_check?.quality_score || result.quality_score || 0;
    if (qualityBar) {
        qualityBar.style.width = `${qualityScore * 100}%`;
    }
    if (qualityText) {
        qualityText.textContent = `${(qualityScore * 100).toFixed(1)}%`;
    }
    
    // Labels
    if (result.labels) {
        if (labelsGrid) {
            labelsGrid.innerHTML = Object.entries(result.labels)
                .map(([key, value]) => `
                    <div class="label-item">
                        <span class="label-key">${key}:</span>
                        <span class="label-value">${Array.isArray(value) ? value.join(', ') : value}</span>
                    </div>
                `).join('');
        }
        if (resultLabels) {
            resultLabels.textContent = JSON.stringify(result.labels, null, 2);
        }
    }
    
    // Full JSON
    if (resultFullJson) {
        resultFullJson.textContent = JSON.stringify(result, null, 2);
    }
    
    showResults();
}

function copyJSONToClipboard() {
    const resultFullJson = document.getElementById('resultFullJson');
    if (resultFullJson) {
        const text = resultFullJson.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const copyBtn = document.getElementById('copyBtn');
            if (copyBtn) {
                const originalText = copyBtn.textContent;
                copyBtn.textContent = '✓ Copied!';
                setTimeout(() => {
                    copyBtn.textContent = originalText;
                }, 2000);
            }
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    }
}

function toggleSection(sectionName) {
    const section = sectionName === 'labels' ? 'labelsContent' : 'jsonContent';
    const expandBtn = sectionName === 'labels' ? 'expandLabels' : 'expandJson';
    
    const content = document.getElementById(section);
    const btn = document.getElementById(expandBtn);
    
    if (content && btn) {
        const isExpanded = !content.classList.contains('hidden');
        content.classList.toggle('hidden');
        btn.textContent = isExpanded ? '▼' : '▲';
    }
}

function showProcessing() {
    processingStatus?.classList.remove('hidden');
    updateProgress({ progress: 0 });
}

function hideProcessing() {
    processingStatus?.classList.add('hidden');
}

function showResults() {
    resultsSection?.classList.remove('hidden');
}

function hideResults() {
    resultsSection?.classList.add('hidden');
}

function showError(message) {
    const errorMessage = document.getElementById('errorMessage');
    if (errorMessage) {
        errorMessage.textContent = message;
    }
    errorSection?.classList.remove('hidden');
}

function hideError() {
    errorSection?.classList.add('hidden');
}



