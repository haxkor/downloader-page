// DOM elements
const urlInput = document.getElementById('urlInput');
const downloadBtn = document.getElementById('downloadBtn');
const statusDiv = document.getElementById('status');
const statusMessage = document.getElementById('statusMessage');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const filesList = document.getElementById('filesList');
const refreshBtn = document.getElementById('refreshBtn');

const chanUrlInput = document.getElementById('chanUrlInput');
const chanDownloadBtn = document.getElementById('chanDownloadBtn');
const chanStatusDiv = document.getElementById('chanStatus');
const chanStatusMessage = document.getElementById('chanStatusMessage');
const chanProgressFill = document.getElementById('chanProgressFill');
const chanProgressText = document.getElementById('chanProgressText');

// State
let currentDownloadId = null;
let statusCheckInterval = null;
let chanDownloadId = null;
let chanStatusInterval = null;

// Event listeners
downloadBtn.addEventListener('click', startDownload);
refreshBtn.addEventListener('click', loadFiles);
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') startDownload();
});
chanDownloadBtn.addEventListener('click', startChanDownload);
chanUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') startChanDownload();
});

// Initialize
loadFiles();

async function startDownload() {
    const url = urlInput.value.trim();
    const format = document.querySelector('input[name="format"]:checked').value;

    if (!url) {
        alert('Please enter a URL');
        return;
    }

    try {
        downloadBtn.disabled = true;
        showStatus(`Starting ${format} download...`, 0);

        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url, format }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Download failed');
        }

        currentDownloadId = data.download_id;
        checkStatus();

    } catch (error) {
        showError(error.message);
        downloadBtn.disabled = false;
    }
}

function checkStatus() {
    if (!currentDownloadId) return;

    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${currentDownloadId}`);
            const data = await response.json();

            if (data.status === 'downloading') {
                showStatus('Downloading...', data.progress);
            } else if (data.status === 'completed') {
                showSuccess('Download completed!', data.filename);
                stopStatusCheck();
                loadFiles();
                urlInput.value = '';
                downloadBtn.disabled = false;
            } else if (data.status === 'error') {
                showError(data.error || 'Download failed');
                stopStatusCheck();
                downloadBtn.disabled = false;
            }
        } catch (error) {
            console.error('Status check error:', error);
        }
    }, 1000);
}

function stopStatusCheck() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
    currentDownloadId = null;
}

function showStatus(message, progress) {
    statusDiv.classList.remove('hidden', 'error', 'success');
    statusMessage.textContent = message;
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
}

function showSuccess(message, filename) {
    statusDiv.classList.remove('hidden', 'error');
    statusDiv.classList.add('success');
    statusMessage.textContent = `${message} (${filename})`;
    progressFill.style.width = '100%';
    progressText.textContent = '100%';
}

function showError(message) {
    statusDiv.classList.remove('hidden', 'success');
    statusDiv.classList.add('error');
    statusMessage.textContent = `Error: ${message}`;
    progressFill.style.width = '0%';
    progressText.textContent = '';
}

async function loadFiles() {
    try {
        const response = await fetch('/files');
        const files = await response.json();

        if (files.length === 0) {
            filesList.innerHTML = '<p class="empty-message">No files downloaded yet</p>';
            return;
        }

        filesList.innerHTML = files.map(file => `
            <div class="file-item">
                <div class="file-info">
                    <div class="file-name">${escapeHtml(file.name)}</div>
                    <div class="file-size">${formatBytes(file.size)}</div>
                </div>
                <a href="${file.url}" class="file-download" download>Download</a>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load files:', error);
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

async function startChanDownload() {
    const url = chanUrlInput.value.trim();
    if (!url) {
        alert('Please enter a 4chan URL');
        return;
    }

    try {
        chanDownloadBtn.disabled = true;
        showChanStatus('Starting download...', 0);

        const response = await fetch('/4chan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Download failed');

        chanDownloadId = data.download_id;
        checkChanStatus();

    } catch (error) {
        showChanError(error.message);
        chanDownloadBtn.disabled = false;
    }
}

function checkChanStatus() {
    if (!chanDownloadId) return;

    chanStatusInterval = setInterval(async () => {
        try {
            const response = await fetch(`/status/${chanDownloadId}`);
            const data = await response.json();

            if (data.status === 'downloading') {
                const msg = data.files_total > 0
                    ? `Downloading ${data.files_done} / ${data.files_total} files...`
                    : 'Downloading...';
                showChanStatus(msg, data.progress);
            } else if (data.status === 'completed') {
                const msg = data.files_total > 1
                    ? `Downloaded ${data.files_total} files`
                    : `Download completed! (${data.filename})`;
                showChanSuccess(msg);
                stopChanStatusCheck();
                loadFiles();
                chanUrlInput.value = '';
                chanDownloadBtn.disabled = false;
            } else if (data.status === 'error') {
                showChanError(data.error || 'Download failed');
                stopChanStatusCheck();
                chanDownloadBtn.disabled = false;
            }
        } catch (error) {
            console.error('Chan status check error:', error);
        }
    }, 1000);
}

function stopChanStatusCheck() {
    if (chanStatusInterval) {
        clearInterval(chanStatusInterval);
        chanStatusInterval = null;
    }
    chanDownloadId = null;
}

function showChanStatus(message, progress) {
    chanStatusDiv.classList.remove('hidden', 'error', 'success');
    chanStatusMessage.textContent = message;
    chanProgressFill.style.width = `${progress}%`;
    chanProgressText.textContent = `${progress}%`;
}

function showChanSuccess(message) {
    chanStatusDiv.classList.remove('hidden', 'error');
    chanStatusDiv.classList.add('success');
    chanStatusMessage.textContent = message;
    chanProgressFill.style.width = '100%';
    chanProgressText.textContent = '100%';
}

function showChanError(message) {
    chanStatusDiv.classList.remove('hidden', 'success');
    chanStatusDiv.classList.add('error');
    chanStatusMessage.textContent = `Error: ${message}`;
    chanProgressFill.style.width = '0%';
    chanProgressText.textContent = '';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
