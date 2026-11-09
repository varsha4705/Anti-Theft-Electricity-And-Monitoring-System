/**
 * Live Monitor — Real-time sensor data with gauges
 */

let monitorInterval = null;
let selectedConsumerId = null;

document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) return;
    initSidebar();
    loadLiveData();
    startAutoRefresh();
});

// ============================================================
// Load Live Data
// ============================================================

async function loadLiveData() {
    const result = await api.getLiveData();

    if (result && result.status === 'success') {
        renderLiveGrid(result.live_data);
    }
}

function renderLiveGrid(data) {
    const grid = document.getElementById('live-grid');
    if (!grid) return;

    if (data.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">📡</div>
                <h3>No Live Data</h3>
                <p>Waiting for sensor readings from ESP32 devices...</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = data.map(reading => {
        const isTheft = reading.is_theft;
        const diffPercent = Math.min((reading.difference / 15) * 100, 100);
        const barColor = isTheft ? '#ef4444' : '#10b981';
        const valueClass = isTheft ? 'danger' : 'normal';

        return `
            <div class="gauge-card ${isTheft ? 'theft-active' : ''}" onclick="showConsumerDetail(${reading.consumer_id})">
                <div class="flex-between mb-1">
                    <div>
                        <div style="font-weight:600; color: var(--text-primary)">${reading.consumer_name}</div>
                        <div class="text-muted" style="font-size:12px">${reading.cons_no} · ${reading.area || 'N/A'}</div>
                    </div>
                    ${isTheft
                        ? '<span class="badge badge-danger badge-dot">THEFT</span>'
                        : '<span class="badge badge-success badge-dot">Normal</span>'
                    }
                </div>

                <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px; margin:20px 0;">
                    <div>
                        <div class="gauge-label">I_in</div>
                        <div style="font-size:22px; font-weight:700; font-family:var(--font-mono); color:var(--accent-primary)">
                            ${reading.i_in}<span class="gauge-unit" style="font-size:12px">A</span>
                        </div>
                    </div>
                    <div>
                        <div class="gauge-label">I_out</div>
                        <div style="font-size:22px; font-weight:700; font-family:var(--font-mono); color:var(--accent-secondary)">
                            ${reading.i_out}<span class="gauge-unit" style="font-size:12px">A</span>
                        </div>
                    </div>
                    <div>
                        <div class="gauge-label">Diff</div>
                        <div class="gauge-value ${valueClass}" style="font-size:22px;">
                            ${reading.difference}<span class="gauge-unit" style="font-size:12px">A</span>
                        </div>
                    </div>
                </div>

                <div class="gauge-bar">
                    <div class="bar-fill" style="width:${diffPercent}%; background:${barColor}"></div>
                </div>

                <div class="flex-between mt-1" style="font-size:11px; color:var(--text-muted)">
                    <span>${reading.voltage}V · ${reading.power}W</span>
                    <span>${timeAgo(reading.timestamp)}</span>
                </div>
            </div>
        `;
    }).join('');
}


// ============================================================
// Consumer Detail Modal
// ============================================================

async function showConsumerDetail(consumerId) {
    selectedConsumerId = consumerId;
    const result = await api.getConsumer(consumerId);

    if (result && result.status === 'success') {
        const c = result.consumer;
        const modal = document.getElementById('consumer-detail-modal');
        if (!modal) return;

        document.getElementById('detail-consumer-name').textContent = c.name;
        document.getElementById('detail-consumer-info').innerHTML = `
            <div class="detail-grid">
                <div class="detail-item">
                    <div class="detail-label">Consumer No</div>
                    <div class="detail-value text-mono">${c.cons_no}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Area</div>
                    <div class="detail-value">${c.area || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Meter ID</div>
                    <div class="detail-value text-mono">${c.meter_id || 'N/A'}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value">${getStatusBadge(c.status)}</div>
                </div>
            </div>
        `;

        // Recent readings chart
        if (c.readings && c.readings.length > 0) {
            const last20 = c.readings.slice(0, 20).reverse();
            createDetailChart(last20);
        }

        openModal('consumer-detail-modal');
    }
}

let detailChart = null;

function createDetailChart(readings) {
    const ctx = document.getElementById('detail-chart');
    if (!ctx) return;

    if (detailChart) detailChart.destroy();

    detailChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: readings.map(r => {
                const d = new Date(r.timestamp);
                return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
            }),
            datasets: [
                {
                    label: 'I_in (A)',
                    data: readings.map(r => r.i_in),
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3
                },
                {
                    label: 'I_out (A)',
                    data: readings.map(r => r.i_out),
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#94a3b8', font: { size: 11 } }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148,163,184,0.06)' },
                    ticks: { color: '#64748b', font: { size: 10 }, maxRotation: 45 }
                },
                y: {
                    grid: { color: 'rgba(148,163,184,0.06)' },
                    ticks: { color: '#64748b', font: { size: 10 } },
                    beginAtZero: true
                }
            }
        }
    });
}


// ============================================================
// Auto Refresh
// ============================================================

function startAutoRefresh() {
    monitorInterval = setInterval(loadLiveData, 5000);
}

function stopAutoRefresh() {
    if (monitorInterval) {
        clearInterval(monitorInterval);
        monitorInterval = null;
    }
}

// Clean up on page leave
window.addEventListener('beforeunload', stopAutoRefresh);
