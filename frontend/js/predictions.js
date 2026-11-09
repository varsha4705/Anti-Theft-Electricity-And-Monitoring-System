/**
 * Predictions — Single & Batch ML Predictions
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) return;
    initSidebar();
    loadPredictionHistory();
    setupDropzone();
});


// ============================================================
// Single Prediction
// ============================================================

async function runSinglePrediction() {
    const form = document.getElementById('single-predict-form');
    if (!form) return;

    const formData = new FormData(form);
    const data = {};

    formData.forEach((value, key) => {
        data[key] = isNaN(value) ? value : parseFloat(value);
    });

    if (Object.keys(data).length === 0) {
        showToast('Please fill in at least one field', 'warning');
        return;
    }

    const btn = document.getElementById('predict-btn');
    const btnText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Predicting...';

    const result = await api.predictSingle(data);

    btn.disabled = false;
    btn.innerHTML = btnText;

    const resultDiv = document.getElementById('prediction-result');
    if (!resultDiv) return;

    if (result && result.status === 'success') {
        const isTheft = result.prediction === 1;
        resultDiv.innerHTML = `
            <div class="prediction-result ${isTheft ? 'theft' : 'normal'}">
                <div class="result-icon">${isTheft ? '🚨' : '✅'}</div>
                <div class="result-label" style="color: ${isTheft ? 'var(--color-danger)' : 'var(--color-success)'}">
                    ${result.label}
                </div>
                <div class="result-confidence">
                    Confidence: ${result.confidence}%
                </div>
            </div>
        `;
        resultDiv.classList.remove('hidden');
    } else {
        showToast(result?.message || 'Prediction failed', 'error');
    }
}


// ============================================================
// Batch Prediction (CSV Upload)
// ============================================================

function setupDropzone() {
    const dropzone = document.getElementById('csv-dropzone');
    const fileInput = document.getElementById('csv-file-input');
    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) handleFileUpload(file);
    });

    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileUpload(file);
    });
}

async function handleFileUpload(file) {
    if (!file.name.endsWith('.csv')) {
        showToast('Please upload a CSV file', 'warning');
        return;
    }

    const dropzone = document.getElementById('csv-dropzone');
    dropzone.innerHTML = `
        <div class="drop-icon"><span class="spinner" style="width:32px;height:32px;border-width:3px;display:inline-block"></span></div>
        <div class="drop-text">Processing ${file.name}...</div>
    `;

    const formData = new FormData();
    formData.append('file', file);

    const result = await api.predictBatch(formData);

    // Reset dropzone
    dropzone.innerHTML = `
        <div class="drop-icon">📁</div>
        <div class="drop-text">Drop CSV file here or click to upload</div>
        <div class="drop-hint">Supports .csv files with consumer data</div>
    `;

    if (result && result.status === 'success') {
        showToast(`Processed ${result.total} records`, 'success');
        renderBatchResults(result);
    } else {
        showToast(result?.message || 'Batch prediction failed', 'error');
    }
}

function renderBatchResults(data) {
    const container = document.getElementById('batch-results');
    if (!container) return;

    container.innerHTML = `
        <div class="card mt-2">
            <div class="card-header">
                <h3>📊 Batch Results — ${data.total} Records</h3>
            </div>
            <div class="card-body">
                <div class="stats-grid" style="margin-bottom:20px">
                    <div class="stat-card">
                        <div class="stat-value text-green">${data.normal_count}</div>
                        <div class="stat-label">Normal</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value text-red">${data.theft_count}</div>
                        <div class="stat-label">Theft Detected</div>
                    </div>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                ${data.results[0]?.cons_no !== undefined ? '<th>Consumer No</th>' : ''}
                                <th>Prediction</th>
                                <th>Confidence</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.results.slice(0, 100).map((r, i) => `
                                <tr>
                                    <td class="td-mono">${i + 1}</td>
                                    ${r.cons_no !== undefined ? `<td class="td-mono">${r.cons_no}</td>` : ''}
                                    <td class="td-bold">${r.label}</td>
                                    <td class="td-mono">${r.confidence}%</td>
                                    <td>${r.prediction === 1
                                        ? '<span class="badge badge-danger badge-dot">Theft</span>'
                                        : '<span class="badge badge-success badge-dot">Normal</span>'
                                    }</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                    ${data.total > 100 ? `<p class="text-muted text-center mt-1" style="font-size:12px">Showing 100 of ${data.total} results</p>` : ''}
                </div>
            </div>
        </div>
    `;
    container.classList.remove('hidden');
}


// ============================================================
// Prediction History
// ============================================================

async function loadPredictionHistory() {
    const result = await api.getPredictionHistory();

    if (result && result.status === 'success') {
        const tbody = document.getElementById('history-tbody');
        if (!tbody) return;

        if (result.predictions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:30px">No prediction history</td></tr>';
            return;
        }

        tbody.innerHTML = result.predictions.map(p => `
            <tr>
                <td class="td-mono">${p.cons_no || '—'}</td>
                <td class="td-bold">${p.consumer_name || 'Manual Input'}</td>
                <td>${p.prediction === 1
                    ? '<span class="badge badge-danger badge-dot">Theft</span>'
                    : '<span class="badge badge-success badge-dot">Normal</span>'
                }</td>
                <td class="td-mono">${p.confidence}%</td>
                <td class="text-muted" style="font-size:12px">${formatDateTime(p.created_at)}</td>
            </tr>
        `).join('');
    }
}
