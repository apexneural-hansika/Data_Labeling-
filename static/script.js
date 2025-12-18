/**
 * Frontend JavaScript for NexusAI data labeling platform
 * Handles file uploads, progress tracking, and result display
 * Enhanced UX with toast notifications, keyboard shortcuts, and better feedback
 */

// Global state
let currentTaskId = null;
let progressInterval = null;
let simulationInterval = null;
let toastContainer = null;

// DOM elements (will be initialized on DOMContentLoaded)
let uploadForm, fileInput, dropZone, filePreview, fileName, fileInfo;
let submitBtn, processingStatus, resultsSection, errorSection;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM elements
    uploadForm = document.getElementById('uploadForm');
    fileInput = document.getElementById('fileInput');
    dropZone = document.getElementById('dropZone');
    filePreview = document.getElementById('filePreview');
    fileName = document.getElementById('fileName');
    fileInfo = document.getElementById('fileInfo');
    submitBtn = document.getElementById('submitBtn');
    processingStatus = document.getElementById('processingStatus');
    resultsSection = document.getElementById('resultsSection');
    errorSection = document.getElementById('errorSection');
    
    // Check if elements exist
    if (!uploadForm || !fileInput || !submitBtn) {
        console.error('Required DOM elements not found. Check HTML structure.');
        return;
    }
    
    initializeEventListeners();
    initializeToastSystem();
    initializeKeyboardShortcuts();
    initializeTooltips();
});

function initializeEventListeners() {
    // File input change
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Form submission
    if (uploadForm) {
        uploadForm.addEventListener('submit', handleFormSubmit);
    }
    
    // Drag and drop
    if (dropZone) {
        dropZone.addEventListener('dragover', handleDragOver);
        dropZone.addEventListener('dragleave', handleDragLeave);
        dropZone.addEventListener('drop', handleDrop);
        dropZone.addEventListener('click', () => {
            if (fileInput) fileInput.click();
        });
    }
    
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
    
    // Download button
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadJSON);
    }
    
    // JSON toggle button
    const toggleJsonView = document.getElementById('toggleJsonView');
    if (toggleJsonView) {
        toggleJsonView.addEventListener('click', () => {
            const jsonView = document.getElementById('resultLabels');
            if (jsonView) {
                const isHidden = jsonView.style.display === 'none';
                jsonView.style.display = isHidden ? 'block' : 'none';
                toggleJsonView.textContent = isHidden ? 'Hide Raw JSON' : 'Show Raw JSON';
            }
        });
    }
    
    // Label search input
    const labelsSearchInput = document.getElementById('labelsSearchInput');
    if (labelsSearchInput) {
        labelsSearchInput.addEventListener('input', filterLabels);
    }
    
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterLabels();
        });
    });
}

// Toast Notification System
function initializeToastSystem() {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
}

function showToast(message, type = 'info', duration = 5000) {
    if (!toastContainer) initializeToastSystem();
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after duration
    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, duration);
    
    return toast;
}

// Keyboard Shortcuts
function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + U: Upload file
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            if (fileInput) fileInput.click();
            showToast('File picker opened', 'info', 2000);
        }
        
        // Ctrl/Cmd + Enter: Submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            if (uploadForm && !submitBtn?.disabled) {
                e.preventDefault();
                uploadForm.dispatchEvent(new Event('submit'));
            }
        }
        
        // Escape: Close errors/toasts
        if (e.key === 'Escape') {
            hideError();
            // Close all toasts
            document.querySelectorAll('.toast').forEach(toast => {
                toast.classList.add('hiding');
                setTimeout(() => toast.remove(), 300);
            });
        }
    });
}

// Tooltips
function initializeTooltips() {
    // Add tooltips to buttons
    const buttons = document.querySelectorAll('[title]');
    buttons.forEach(btn => {
        btn.addEventListener('mouseenter', showTooltip);
        btn.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(e) {
    const title = e.target.getAttribute('title');
    if (!title) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = title;
    tooltip.style.cssText = `
        position: absolute;
        background: rgba(0, 0, 0, 0.9);
        color: white;
        padding: 8px 12px;
        border-radius: 6px;
        font-size: 12px;
        pointer-events: none;
        z-index: 10000;
        white-space: nowrap;
    `;
    
    document.body.appendChild(tooltip);
    const rect = e.target.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
    
    e.target._tooltip = tooltip;
    e.target.removeAttribute('title');
}

function hideTooltip(e) {
    if (e.target._tooltip) {
        e.target._tooltip.remove();
        delete e.target._tooltip;
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
        // Create a new FileList-like object and assign to input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(files[0]);
        fileInput.files = dataTransfer.files;
        displayFileInfo(files[0]);
    }
}

function displayFileInfo(file) {
    if (fileName) {
        fileName.textContent = file.name;
    }
    if (fileInfo) {
        fileInfo.innerHTML = `
            <div class="file-details">
                <span>Size: ${formatFileSize(file.size)}</span>
                <span>Type: ${file.type || 'Unknown'}</span>
            </div>
        `;
    }
    if (filePreview) {
        filePreview.innerHTML = `
            <div class="file-preview-enhanced">
                <div class="file-preview-icon">${getFileIcon(file.name)}</div>
                <div class="file-preview-details">
                    <div class="file-preview-name">${file.name}</div>
                    <div class="file-preview-meta">
                        <span>${formatFileSize(file.size)}</span>
                        <span>${file.type || 'Unknown type'}</span>
                    </div>
                </div>
                <button class="file-preview-remove" onclick="clearFileSelection()" title="Remove file">Remove</button>
            </div>
        `;
    }
    showToast(`File selected: ${file.name}`, 'success', 3000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
    
    if (!fileInput || !submitBtn) {
        console.error('Required elements not found');
        showToast('System error: Form elements not found', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    if (!file) {
        showToast('Please select a file to upload', 'warning', 3000);
        showError('Please select a file to upload');
        return;
    }
    
    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showToast(`File size (${formatFileSize(file.size)}) exceeds 100MB limit`, 'error');
        showError('File size exceeds 100MB limit');
        return;
    }
    
    // Reset UI
    hideError();
    hideResults();
    showProcessing();
    
    // START ANIMATIONS IMMEDIATELY - don't wait for API response
    console.log('Starting immediate visual feedback');
    
    // START ANIMATIONS IMMEDIATELY using requestAnimationFrame for smooth start
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            const steps = ['router', 'extractor', 'classifier', 'labeler', 'quality', 'output'];
            const firstStep = document.querySelector(`[data-step="${steps[0]}"]`);
            
            if (firstStep) {
                // Remove any existing classes first
                firstStep.classList.remove('active', 'completed', 'pending');
                // Force reflow
                void firstStep.offsetHeight;
                
                // Add active class
                firstStep.classList.add('active');
                // Force another reflow to trigger animation
                void firstStep.offsetHeight;
                
                const statusIndicator = firstStep.querySelector('.step-status');
                if (statusIndicator) {
                    statusIndicator.className = 'step-status';
                    void statusIndicator.offsetHeight; // Force reflow
                    // Trigger animation by toggling
                    statusIndicator.style.animation = 'none';
                    void statusIndicator.offsetHeight;
                    statusIndicator.style.animation = '';
                }
                
                // Update description with animation
                const stepDesc = firstStep.querySelector('.step-desc');
                if (stepDesc) {
                    stepDesc.textContent = 'Classifying modality...';
                    stepDesc.style.color = 'var(--primary-color)';
                    stepDesc.style.animation = 'text-pulse 2s ease-in-out infinite';
                }
                
                // Update icon to trigger glow animation
                const stepIcon = firstStep.querySelector('.step-icon');
                if (stepIcon) {
                    stepIcon.style.animation = 'none';
                    void stepIcon.offsetHeight;
                    stepIcon.style.animation = '';
                }
                
                console.log('✅ First step activated with animations:', steps[0]);
            } else {
                console.error('❌ First step not found!');
            }
            
            // Start progress bar immediately with animation
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            if (progressFill && progressText) {
                progressFill.style.width = '0%';
                progressText.textContent = '0%';
                void progressFill.offsetHeight; // Force reflow
                
                // Animate to 3% immediately
                setTimeout(() => {
                    progressFill.style.width = '3%';
                    progressText.textContent = '3%';
                    void progressFill.offsetHeight;
                    console.log('✅ Progress bar started at 3%');
                }, 150);
            } else {
                console.error('❌ Progress elements not found!', { progressFill, progressText });
            }
        });
    });
    
    // Disable form
    submitBtn.disabled = true;
    submitBtn.classList.add('submit-btn-enhanced');
    const btnText = submitBtn.querySelector('.btn-text');
    if (btnText) {
        btnText.textContent = 'Processing...';
    }
    
    showToast('Uploading file...', 'info', 2000);
    
    try {
        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        
        console.log('Uploading file:', file.name, 'Size:', file.size);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            let errorMessage = `HTTP ${response.status}`;
            try {
                const error = await response.json();
                errorMessage = error.error || errorMessage;
            } catch (e) {
                // If response is not JSON, use status text
                errorMessage = response.statusText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        console.log('Upload result:', result);
        
        // Check if it's an async task
        if (result.task_id) {
            currentTaskId = result.task_id;
            showToast('Processing started. This may take a few moments...', 'info', 4000);
            startProgressPolling(result.task_id);
        } else {
            // Synchronous result - simulate progress quickly
            simulateQuickProgress(() => {
                showToast('Processing complete!', 'success', 3000);
                displayResults(result);
                hideProcessing();
                // Scroll to results
                setTimeout(() => {
                    resultsSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            });
        }
        
    } catch (error) {
        console.error('Upload error:', error);
        const errorMsg = error.message || 'Failed to process file. Please check console for details.';
        showToast(errorMsg, 'error', 5000);
        showError(errorMsg);
        hideProcessing();
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('submit-btn-enhanced');
            const btnText = submitBtn.querySelector('.btn-text');
            if (btnText) {
                btnText.textContent = 'Process File';
            }
        }
    }
}

function startProgressPolling(taskId) {
    console.log('Starting progress polling for task:', taskId);
    
    if (progressInterval) {
        clearInterval(progressInterval);
        progressInterval = null;
    }
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
    }
    
    // Initialize simulated progress
    const steps = ['router', 'extractor', 'classifier', 'labeler', 'quality', 'output'];
    let currentStepIndex = 0;
    let stepStartTime = Date.now();
    let lastProgress = 0;
    let isTransitioning = false; // Flag to prevent multiple transitions
    
    // Ensure processing section is visible
    if (processingStatus) {
        processingStatus.classList.remove('hidden');
    }
    
    // Ensure first step is active (might already be set from form submit)
    const firstStep = document.querySelector(`[data-step="${steps[0]}"]`);
    if (firstStep && !firstStep.classList.contains('active')) {
        console.log('Activating first step in startProgressPolling');
        updateStepStatus(steps[0], 'active');
    } else if (firstStep) {
        console.log('First step already active');
    }
    
    // Ensure progress is visible (might already be set from form submit)
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    if (progressFill && progressText) {
        const currentWidth = progressFill.style.width || '0%';
        const currentPercent = parseFloat(currentWidth);
        if (currentPercent < 3) {
            progressFill.style.width = '3%';
            progressText.textContent = '3%';
            void progressFill.offsetHeight;
            console.log('Progress set to 3% in startProgressPolling');
        }
    }
    
    // Start simulation immediately (don't wait for first API call)
    // Use a shorter interval for more responsive updates
    console.log('Starting simulation interval immediately');
    
    // Run first update immediately
    const runSimulation = () => {
        const elapsed = Date.now() - stepStartTime;
        const stepDuration = 2000; // 2 seconds per step to cycle through all 6 steps faster
        
        // Calculate progress based on current step
        const baseProgress = (currentStepIndex / steps.length) * 100;
        const stepProgress = Math.min((elapsed / stepDuration) * (100 / steps.length), 100 / steps.length);
        let progress = Math.min(baseProgress + stepProgress, 95); // Cap at 95% until complete
        
        // Ensure progress always increases
        if (progress <= lastProgress) {
            progress = lastProgress + 0.8; // Small increment
        }
        lastProgress = progress;
        
        // Update progress bar - ensure elements exist
        if (progressFill && progressText) {
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}%`;
            // Force reflow to ensure animation
            void progressFill.offsetHeight;
        } else {
            console.warn('Progress elements missing in simulation');
        }
        
        // Move to next step if current step is done (only once per step)
        if (elapsed >= stepDuration && currentStepIndex < steps.length - 1 && !isTransitioning) {
            isTransitioning = true; // Prevent multiple transitions
            
            const completedStepName = steps[currentStepIndex];
            
            // Complete current step
            updateStepStatus(completedStepName, 'completed');
            
            // Move to next step
            currentStepIndex++;
            const nextStepName = steps[currentStepIndex];
            
            // Reset timing IMMEDIATELY (not in setTimeout) so next step timing is correct
            stepStartTime = Date.now();
            lastProgress = (currentStepIndex / steps.length) * 100; // Reset to base progress
            
            // Activate next step with full animation
            const nextStep = document.querySelector(`[data-step="${nextStepName}"]`);
            if (nextStep) {
                // Remove any existing classes
                nextStep.classList.remove('active', 'completed', 'pending');
                void nextStep.offsetHeight; // Force reflow
                
                // Add active class
                nextStep.classList.add('active');
                void nextStep.offsetHeight; // Force reflow again
                
                    // Update status indicator with animation reset
                    const statusIndicator = nextStep.querySelector('.step-status');
                    if (statusIndicator) {
                        statusIndicator.className = 'step-status';
                        // Force reflow
                        void statusIndicator.offsetHeight;
                        // Reset and restart animation explicitly
                        statusIndicator.style.animation = 'none';
                        void statusIndicator.offsetHeight;
                        // Use the exact animation from CSS
                        statusIndicator.style.animation = 'status-bounce 1.2s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite';
                        void statusIndicator.offsetHeight;
                    }
                    
                    // Update icon animation
                    const stepIcon = nextStep.querySelector('.step-icon');
                    if (stepIcon) {
                        // Reset and restart animation explicitly
                        stepIcon.style.animation = 'none';
                        void stepIcon.offsetHeight;
                        // Use the exact animation from CSS
                        stepIcon.style.animation = 'icon-wave 2s ease-in-out infinite';
                        void stepIcon.offsetHeight;
                    }
                    
                    // Update icon SVG animation
                    const stepIconSvg = nextStep.querySelector('.step-icon svg');
                    if (stepIconSvg) {
                        stepIconSvg.style.animation = 'none';
                        void stepIconSvg.offsetHeight;
                        stepIconSvg.style.animation = 'icon-float 3s ease-in-out infinite';
                        void stepIconSvg.offsetHeight;
                    }
                
                // Update description with animation
                const stepDesc = nextStep.querySelector('.step-desc');
                if (stepDesc) {
                    const descriptions = {
                        'router': 'Classifying modality...',
                        'extractor': 'Extracting content...',
                        'classifier': 'Assigning category...',
                        'labeler': 'Generating labels...',
                        'quality': 'Validating quality...',
                        'output': 'Formatting output...'
                    };
                    stepDesc.textContent = descriptions[nextStepName] || 'Processing...';
                    stepDesc.style.color = 'var(--primary-color)';
                    stepDesc.style.animation = 'text-pulse 2s ease-in-out infinite';
                }
                
                } else {
                    console.warn(`Step element not found: ${nextStepName}`);
                }
            
            // Also call updateStepStatus to ensure consistency
            updateStepStatus(nextStepName, 'active');
            
            // Reset flag to allow next transition
            isTransitioning = false;
        }
        
        // Check if all steps are complete
        if (currentStepIndex >= steps.length - 1 && elapsed >= stepDuration) {
            // Complete the last step
            updateStepStatus(steps[currentStepIndex], 'completed');
            if (progressFill && progressText) {
                progressFill.style.width = '100%';
                progressText.textContent = '100%';
                void progressFill.offsetHeight;
            }
        }
    };
    
    // Run immediately
    runSimulation();
    
    // Then continue with interval
    simulationInterval = setInterval(runSimulation, 50); // Update every 50ms for very smooth animation
    
    progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/task/${taskId}`);
            if (!response.ok) {
                throw new Error('Failed to get task status');
            }
            
            const task = await response.json();
            
            // Use actual progress if available
            if (task.progress && task.progress > 0) {
                if (simulationInterval) {
                    clearInterval(simulationInterval);
                    simulationInterval = null;
                }
                const progressPerStep = 100 / steps.length;
                const estimatedStep = Math.min(Math.floor(task.progress / progressPerStep), steps.length - 1);
                
                // Update completed steps
                for (let i = 0; i < estimatedStep; i++) {
                    updateStepStatus(steps[i], 'completed');
                }
                
                // Update active step
                if (estimatedStep < steps.length) {
                    updateStepStatus(steps[estimatedStep], 'active');
                }
                
                updateProgress({ ...task, progress: task.progress });
            }
            
            if (task.status === 'completed') {
                if (simulationInterval) {
                    clearInterval(simulationInterval);
                    simulationInterval = null;
                }
                // Mark all steps as completed
                steps.forEach(step => updateStepStatus(step, 'completed'));
                updateProgress({ ...task, progress: 100 });
                
                clearInterval(progressInterval);
                progressInterval = null;
                displayResults(task.result);
                hideProcessing();
            } else if (task.status === 'failed') {
                if (simulationInterval) {
                    clearInterval(simulationInterval);
                    simulationInterval = null;
                }
                clearInterval(progressInterval);
                progressInterval = null;
                showError(task.error || 'Processing failed');
                hideProcessing();
            }
        } catch (error) {
            console.error('Progress polling error:', error);
            // Continue with simulation even if API call fails
        }
    }, 2000); // Poll API every 2 seconds
}

function updateProgress(task) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    if (progressFill && progressText) {
        const progress = Math.min(Math.max(task.progress || 0, 0), 100); // Clamp between 0-100
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}%`;
        
        // Force reflow to ensure animation
        void progressFill.offsetHeight;
    } else {
        console.warn('Progress bar elements not found:', { progressFill, progressText });
    }
    
    // Update step statuses from task if provided
    if (task.current_step) {
        updateStepStatus(task.current_step, 'active');
    }
    
    if (task.completed_steps && Array.isArray(task.completed_steps)) {
        task.completed_steps.forEach(step => {
            updateStepStatus(step, 'completed');
        });
    }
}

function updateStepStatus(stepName, status) {
    const step = document.querySelector(`[data-step="${stepName}"]`);
    if (!step) {
        console.warn(`Step not found: ${stepName}`);
        return;
    }
    
    // Remove previous status classes
    step.classList.remove('active', 'completed', 'pending');
    // Force reflow before adding class to trigger animation
    void step.offsetHeight;
    
    // Add new status class to the step element with animation trigger
    if (status === 'active' || status === 'completed') {
        step.classList.add(status);
        // Force another reflow after adding class
        void step.offsetHeight;
    }
    
    // Update status indicator - CSS uses .step.active .step-status, so we don't add class to indicator
    const statusIndicator = step.querySelector('.step-status');
    if (statusIndicator) {
        // Reset to base class - CSS will style it based on parent .step.active
        statusIndicator.className = 'step-status';
        // Force reflow to trigger animation
        void statusIndicator.offsetHeight;
        
        // If active, reset animation to ensure it triggers
        if (status === 'active') {
            statusIndicator.style.animation = 'none';
            void statusIndicator.offsetHeight;
            statusIndicator.style.animation = 'status-bounce 1.2s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite';
            void statusIndicator.offsetHeight;
        }
    }
    
    // Update step icon animation
    const stepIcon = step.querySelector('.step-icon');
    if (stepIcon && status === 'active') {
        // Reset animation to ensure it triggers
        stepIcon.style.animation = 'none';
        void stepIcon.offsetHeight;
        stepIcon.style.animation = 'icon-wave 2s ease-in-out infinite';
        void stepIcon.offsetHeight;
    }
    
    // Update step icon SVG animation
    const stepIconSvg = step.querySelector('.step-icon svg');
    if (stepIconSvg && status === 'active') {
        stepIconSvg.style.animation = 'none';
        void stepIconSvg.offsetHeight;
        stepIconSvg.style.animation = 'icon-float 3s ease-in-out infinite';
        void stepIconSvg.offsetHeight;
    }
    
    // Update step description based on status
    const stepDesc = step.querySelector('.step-desc');
    if (stepDesc) {
        if (status === 'active') {
            const descriptions = {
                'router': 'Classifying modality...',
                'extractor': 'Extracting content...',
                'classifier': 'Assigning category...',
                'labeler': 'Generating labels...',
                'quality': 'Validating quality...',
                'output': 'Formatting output...'
            };
            stepDesc.textContent = descriptions[stepName] || 'Processing...';
            stepDesc.style.color = 'var(--primary-color)';
            // Add pulsing animation to description
            stepDesc.style.animation = 'text-pulse 2s ease-in-out infinite';
        } else if (status === 'completed') {
            stepDesc.textContent = 'Completed ✓';
            stepDesc.style.color = 'var(--success-color)';
            stepDesc.style.animation = 'none';
        } else {
            stepDesc.style.color = 'var(--text-secondary)';
            stepDesc.style.animation = 'none';
        }
    }
    
    // Force final reflow to ensure CSS transitions work
    void step.offsetHeight;
    
    console.log(`📊 Step "${stepName}" set to "${status}"`);
}

function displayResults(result) {
    // Update result cards
    const resultFileName = document.getElementById('resultFileName');
    const resultModality = document.getElementById('resultModality');
    const resultCategory = document.getElementById('resultCategory');
    const resultQuality = document.getElementById('resultQuality');
    const qualityBarFill = document.getElementById('qualityBarFill');
    const qualityPercentage = document.getElementById('qualityPercentage');
    const qualityStatusBadge = document.getElementById('qualityStatusBadge');
    const labelsVisualGrid = document.getElementById('labelsVisualGrid');
    const resultLabels = document.getElementById('resultLabels');
    const resultFullJson = document.getElementById('resultFullJson');
    const processingTime = document.getElementById('processingTime');
    const confidenceScore = document.getElementById('confidenceScore');
    const agentCount = document.getElementById('agentCount');
    const labelCountBadge = document.getElementById('labelCountBadge');
    
    if (resultFileName) resultFileName.textContent = result.file_name || '-';
    if (resultModality) {
        const modalityEl = resultModality;
        modalityEl.textContent = result.modality || '-';
        modalityEl.className = 'badge badge-modality';
    }
    if (resultCategory) {
        const categoryEl = resultCategory;
        categoryEl.textContent = result.category || '-';
        categoryEl.className = 'badge badge-category';
    }
    
    // Quality score with enhanced display
    const qualityScore = result.quality_check?.quality_score || result.quality_score || 0;
    const qualityStatus = result.quality_check?.quality_status || result.quality_status || 'unknown';
    
    if (qualityBarFill) {
        qualityBarFill.style.width = `${qualityScore * 100}%`;
    }
    if (qualityPercentage) {
        qualityPercentage.textContent = `${(qualityScore * 100).toFixed(1)}%`;
    }
    if (qualityStatusBadge) {
        qualityStatusBadge.textContent = qualityStatus;
        qualityStatusBadge.className = `quality-status-badge ${qualityStatus}`;
    }
    
    // Processing time and confidence
    if (processingTime) {
        if (result.processing_time !== undefined) {
            processingTime.textContent = `${result.processing_time.toFixed(2)}s`;
        } else {
            processingTime.textContent = '-';
        }
    }
    if (confidenceScore) {
        const confidence = result.confidence || result.label_confidence || result.metadata?.confidence || 0;
        confidenceScore.textContent = `${(confidence * 100).toFixed(0)}%`;
    }
    
    // Agent count - Always show 6 agents (Router, Extractor, Classifier, Labeler, Quality, Output)
    if (agentCount) {
        agentCount.textContent = '6';
    }
    
    // Labels with enhanced visualization
    if (result.labels) {
        const labelEntries = Object.entries(result.labels);
        const labelCount = labelEntries.length;
        
        if (labelCountBadge) {
            labelCountBadge.textContent = `${labelCount} ${labelCount === 1 ? 'label' : 'labels'}`;
        }
        
        // Visual grid for labels
        if (labelsVisualGrid) {
            labelsVisualGrid.innerHTML = labelEntries
                .map(([key, value]) => {
                    let displayValue;
                    let valueType = 'text';
                    
                    if (Array.isArray(value)) {
                        displayValue = value.map(v => `<span class="label-tag">${escapeHtml(String(v))}</span>`).join('');
                        valueType = 'array';
                    } else if (typeof value === 'object' && value !== null) {
                        displayValue = `<pre class="label-json">${escapeHtml(JSON.stringify(value, null, 2))}</pre>`;
                        valueType = 'object';
                    } else {
                        displayValue = escapeHtml(String(value));
                        valueType = 'text';
                    }
                    
                    return `
                        <div class="label-visual-card" data-label-key="${escapeHtml(key.toLowerCase())}" data-value-type="${valueType}">
                            <div class="label-card-key">${escapeHtml(key)}</div>
                            <div class="label-card-value ${Array.isArray(value) ? 'array' : ''}">${displayValue}</div>
                        </div>
                    `;
                }).join('');
            
            // Initialize search and filter
            initializeLabelSearch();
            updateLabelCount();
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
    
    // Show success toast
    showToast(`File processed successfully! Quality: ${(qualityScore * 100).toFixed(0)}%`, 'success', 4000);
}

// Label Search and Filter Functions
function initializeLabelSearch() {
    const labelsSearchInput = document.getElementById('labelsSearchInput');
    if (labelsSearchInput) {
        labelsSearchInput.value = '';
    }
    
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        if (btn.dataset.filter === 'all') {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function filterLabels() {
    const searchInput = document.getElementById('labelsSearchInput');
    const activeFilter = document.querySelector('.filter-btn.active');
    const filterType = activeFilter ? activeFilter.dataset.filter : 'all';
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    const labelCards = document.querySelectorAll('.label-visual-card');
    let visibleCount = 0;
    
    labelCards.forEach(card => {
        const labelKey = card.dataset.labelKey || '';
        const valueType = card.dataset.valueType || '';
        const cardText = card.textContent.toLowerCase();
        
        // Check filter type
        let matchesFilter = filterType === 'all' || valueType === filterType;
        
        // Check search term
        let matchesSearch = !searchTerm || 
                           labelKey.includes(searchTerm) || 
                           cardText.includes(searchTerm);
        
        if (matchesFilter && matchesSearch) {
            card.classList.remove('hidden');
            visibleCount++;
        } else {
            card.classList.add('hidden');
        }
    });
    
    updateLabelCount(visibleCount, labelCards.length);
}

function updateLabelCount(visible = null, total = null) {
    const visibleCountEl = document.getElementById('visibleLabelCount');
    const totalCountEl = document.getElementById('totalLabelCount');
    
    if (visible === null || total === null) {
        const labelCards = document.querySelectorAll('.label-visual-card');
        const visibleCards = Array.from(labelCards).filter(card => !card.classList.contains('hidden'));
        visible = visibleCards.length;
        total = labelCards.length;
    }
    
    if (visibleCountEl) visibleCountEl.textContent = visible;
    if (totalCountEl) totalCountEl.textContent = total;
}

// Make clearFileSelection globally accessible
window.clearFileSelection = function() {
    if (fileInput) {
        fileInput.value = '';
    }
    if (fileName) fileName.textContent = '';
    if (fileInfo) fileInfo.innerHTML = '';
    if (filePreview) filePreview.innerHTML = '';
    showToast('File selection cleared', 'info', 2000);
};

function downloadJSON() {
    const resultFullJson = document.getElementById('resultFullJson');
    if (resultFullJson && resultFullJson.textContent && resultFullJson.textContent !== '-') {
        const data = resultFullJson.textContent;
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `labeling_result_${new Date().getTime()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showToast('JSON file downloaded', 'success', 3000);
    } else {
        showToast('No results to download', 'warning', 3000);
    }
}

function copyJSONToClipboard() {
    const resultFullJson = document.getElementById('resultFullJson');
    if (resultFullJson && resultFullJson.textContent && resultFullJson.textContent !== '-') {
        const text = resultFullJson.textContent;
        navigator.clipboard.writeText(text).then(() => {
            const copyBtn = document.getElementById('copyBtn');
            if (copyBtn) {
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20 6L9 17l-5-5"></path></svg>Copied!';
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                }, 2000);
            }
            showToast('JSON copied to clipboard!', 'success', 3000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            showToast('Failed to copy to clipboard', 'error', 3000);
        });
    } else {
        showToast('No results to copy', 'warning', 3000);
    }
}

function toggleSection(sectionName) {
    const section = sectionName === 'labels' ? 'labelsContent' : 'jsonContent';
    const expandBtn = sectionName === 'labels' ? 'expandLabels' : 'expandJson';
    const sectionContainer = sectionName === 'labels' 
        ? document.getElementById('labelsHeader')?.closest('.result-section')
        : document.getElementById('jsonHeader')?.closest('.result-section');
    
    if (sectionContainer && expandBtn) {
        const btn = document.getElementById(expandBtn);
        const isExpanded = sectionContainer.classList.contains('expanded');
        
        // Toggle expanded class on the container (not the content)
        sectionContainer.classList.toggle('expanded');
        
        // Update button text
        if (btn) {
            btn.textContent = isExpanded ? '▲' : '▼';
        }
    }
}

function showProcessing() {
    console.log('showProcessing called');
    if (processingStatus) {
        processingStatus.classList.remove('hidden');
        console.log('Processing status section shown');
    } else {
        console.error('Processing status element not found!');
    }
    
    // Reset all step statuses
    const allSteps = document.querySelectorAll('.step');
    console.log('Found steps:', allSteps.length);
    allSteps.forEach(step => {
        step.classList.remove('active', 'completed', 'expanded');
        const statusIndicator = step.querySelector('.step-status');
        if (statusIndicator) {
            statusIndicator.className = 'step-status';
        }
        const stepDesc = step.querySelector('.step-desc');
        if (stepDesc) {
            const descriptions = {
                'router': 'Classifying modality...',
                'extractor': 'Extracting content...',
                'classifier': 'Assigning category...',
                'labeler': 'Generating labels...',
                'quality': 'Validating quality...',
                'output': 'Formatting output...'
            };
            const stepName = step.getAttribute('data-step');
            stepDesc.textContent = descriptions[stepName] || 'Waiting...';
            stepDesc.style.color = 'var(--text-secondary)';
            stepDesc.style.animation = 'none';
        }
    });
    
    // Reset progress bar
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    if (progressFill && progressText) {
        progressFill.style.width = '0%';
        progressText.textContent = '0%';
        void progressFill.offsetHeight; // Force reflow
    }
    console.log('Processing UI reset complete');
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
    if (errorSection) {
        errorSection.classList.remove('hidden');
        errorSection.classList.add('error-card-enhanced');
        
        // Add retry button if not exists
        const errorCard = errorSection.querySelector('.error-card');
        if (errorCard && !errorCard.querySelector('.error-actions')) {
            const errorActions = document.createElement('div');
            errorActions.className = 'error-actions';
            const dismissBtn = document.createElement('button');
            dismissBtn.className = 'error-action-btn';
            dismissBtn.textContent = 'Dismiss';
            dismissBtn.onclick = hideError;
            const reloadBtn = document.createElement('button');
            reloadBtn.className = 'error-action-btn';
            reloadBtn.textContent = 'Reload Page';
            reloadBtn.onclick = () => location.reload();
            errorActions.appendChild(dismissBtn);
            errorActions.appendChild(reloadBtn);
            errorCard.appendChild(errorActions);
        }
    }
    
    // Scroll to error
    setTimeout(() => {
        errorSection?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

function hideError() {
    if (errorSection) {
        errorSection.classList.add('hidden');
        errorSection.classList.remove('error-card-enhanced');
        // Remove error actions if they exist
        const errorActions = errorSection.querySelector('.error-actions');
        if (errorActions) {
            errorActions.remove();
        }
    }
}

// Make hideError globally accessible
window.hideError = hideError;

// Simulate quick progress for synchronous responses
function simulateQuickProgress(callback) {
    const steps = ['router', 'extractor', 'classifier', 'labeler', 'quality', 'output'];
    let currentStep = 0;
    let progress = 0;
    
    const progressInterval = setInterval(() => {
        // Update progress bar
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressFill && progressText) {
            progress += 15;
            if (progress > 100) progress = 100;
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}%`;
        }
        
        // Update steps
        if (currentStep < steps.length) {
            // Mark previous step as completed
            if (currentStep > 0) {
                updateStepStatus(steps[currentStep - 1], 'completed');
            }
            // Mark current step as active
            updateStepStatus(steps[currentStep], 'active');
            currentStep++;
        }
        
        // When done, mark all as completed and call callback
        if (progress >= 100 && currentStep >= steps.length) {
            steps.forEach(step => updateStepStatus(step, 'completed'));
            clearInterval(progressInterval);
            setTimeout(callback, 500);
        }
    }, 300); // Update every 300ms for quick simulation
}

// Toggle step details for interactive pipeline
window.toggleStepDetails = function(stepElement) {
    stepElement.classList.toggle('expanded');
    
    // Close other expanded steps (optional - remove if you want multiple open)
    const allSteps = document.querySelectorAll('.step');
    allSteps.forEach(step => {
        if (step !== stepElement && step.classList.contains('expanded')) {
            step.classList.remove('expanded');
        }
    });
};

