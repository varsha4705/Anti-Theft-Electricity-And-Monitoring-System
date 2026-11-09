/**
 * Dashboard — Charts & Statistics
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) return;
    initSidebar();
    loadDashboard();
});

async function loadDashboard() {
    await Promise.all([
        loadStats(),
        loadCharts()
    ]);
}

// ============================================================
// Dashboard Stats
// ============================================================

async function loadStats() {
    const result = await api.getDashboardStats();

    if (result && result.status === 'success') {
        const s = result.stats;

        animateCounter(document.getElementById('stat-total-consumers'), s.total_consumers);
        animateCounter(document.getElementById('stat-theft-detected'), s.theft_detected);
        animateCounter(document.getElementById('stat-normal-users'), s.normal_users);
        document.getElementById('stat-model-accuracy').textContent = s.model_accuracy;
        animateCounter(document.getElementById('stat-unread-alerts'), s.unread_alerts);
        animateCounter(document.getElementById('stat-total-readings'), s.total_readings);

        // Recent alerts
        const alertsList = document.getElementById('recent-alerts-list');
        if (alertsList && result.recent_alerts) {
            alertsList.innerHTML = result.recent_alerts.map(alert => `
                <div class="alert-item ${!alert.is_read ? 'unread' : ''} ${alert.severity === 'critical' ? 'critical' : ''}">
                    <div class="alert-icon" style="background: ${alert.severity === 'critical' ? 'var(--color-danger-bg)' : 'var(--color-warning-bg)'}; color: ${alert.severity === 'critical' ? 'var(--color-danger)' : 'var(--color-warning)'}">
                        ${alert.severity === 'critical' ? '🚨' : '⚡'}
                    </div>
                    <div class="alert-content">
                        <div class="alert-title">${alert.consumer_name || 'Unknown'} (${alert.cons_no || '—'})</div>
                        <div class="alert-message">${alert.message}</div>
                        <div class="alert-time">${timeAgo(alert.created_at)}</div>
                    </div>
                    ${getSeverityBadge(alert.severity)}
                </div>
            `).join('');

            if (result.recent_alerts.length === 0) {
                alertsList.innerHTML = '<div class="empty-state"><p class="text-muted">No recent alerts</p></div>';
            }
        }
    }
}

// ============================================================
// Charts
// ============================================================

let trendChart, ratioChart, areaChart, hourlyChart;

async function loadCharts() {
    const result = await api.getChartData();

    if (result && result.status === 'success') {
        createTrendChart(result.daily_trends);
        createRatioChart(result.theft_ratio);
        createAreaChart(result.area_data);
        createHourlyChart(result.hourly_data);
    }
}

function createTrendChart(data) {
    const ctx = document.getElementById('trend-chart');
    if (!ctx) return;

    if (trendChart) trendChart.destroy();

    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => {
                const date = new Date(d.date);
                return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
            }),
            datasets: [
                {
                    label: 'Theft Readings',
                    data: data.map(d => d.theft_count),
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#ef4444',
                    pointBorderColor: '#ef4444',
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Normal Readings',
                    data: data.map(d => d.normal_count),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#10b981',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: getChartOptions('Readings Over Time')
    });
}

function createRatioChart(data) {
    const ctx = document.getElementById('ratio-chart');
    if (!ctx) return;

    if (ratioChart) ratioChart.destroy();

    ratioChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Theft', 'Normal'],
            datasets: [{
                data: [data.theft, data.normal],
                backgroundColor: [
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(16, 185, 129, 0.8)'
                ],
                borderColor: [
                    '#ef4444',
                    '#10b981'
                ],
                borderWidth: 2,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#94a3b8',
                        font: { family: 'Inter', size: 12 },
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                title: {
                    display: true,
                    text: 'Theft vs Normal Ratio',
                    color: '#f1f5f9',
                    font: { family: 'Inter', size: 14, weight: '600' },
                    padding: { bottom: 16 }
                }
            }
        }
    });
}

function createAreaChart(data) {
    const ctx = document.getElementById('area-chart');
    if (!ctx) return;

    if (areaChart) areaChart.destroy();

    const colors = [
        '#06b6d4', '#8b5cf6', '#ef4444', '#f59e0b', '#10b981',
        '#3b82f6', '#ec4899', '#f97316', '#14b8a6', '#6366f1'
    ];

    areaChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.area),
            datasets: [{
                label: 'Theft Cases',
                data: data.map(d => d.theft_count),
                backgroundColor: data.map((_, i) => colors[i % colors.length] + '40'),
                borderColor: data.map((_, i) => colors[i % colors.length]),
                borderWidth: 1,
                borderRadius: 6,
                barPercentage: 0.6
            }]
        },
        options: getChartOptions('Theft by Area')
    });
}

function createHourlyChart(data) {
    const ctx = document.getElementById('hourly-chart');
    if (!ctx) return;

    if (hourlyChart) hourlyChart.destroy();

    // Fill missing hours
    const fullData = Array.from({ length: 24 }, (_, i) => {
        const found = data.find(d => d.hour === i);
        return found ? found.theft_count : 0;
    });

    hourlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Array.from({ length: 24 }, (_, i) => `${i}:00`),
            datasets: [{
                label: 'Theft Detections',
                data: fullData,
                backgroundColor: 'rgba(139, 92, 246, 0.4)',
                borderColor: '#8b5cf6',
                borderWidth: 1,
                borderRadius: 4,
                barPercentage: 0.7
            }]
        },
        options: getChartOptions('Theft by Hour of Day')
    });
}

function getChartOptions(title) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                align: 'end',
                labels: {
                    color: '#94a3b8',
                    font: { family: 'Inter', size: 11 },
                    usePointStyle: true,
                    pointStyle: 'circle',
                    padding: 16
                }
            },
            title: {
                display: true,
                text: title,
                color: '#f1f5f9',
                font: { family: 'Inter', size: 14, weight: '600' },
                padding: { bottom: 16 }
            }
        },
        scales: {
            x: {
                grid: { color: 'rgba(148, 163, 184, 0.06)' },
                ticks: {
                    color: '#64748b',
                    font: { family: 'Inter', size: 10 },
                    maxRotation: 45
                }
            },
            y: {
                grid: { color: 'rgba(148, 163, 184, 0.06)' },
                ticks: {
                    color: '#64748b',
                    font: { family: 'Inter', size: 10 }
                },
                beginAtZero: true
            }
        }
    };
}

// Auto-refresh every 30 seconds
setInterval(loadStats, 30000);
