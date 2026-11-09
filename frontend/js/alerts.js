/**
 * Alerts — Alert Management & Filtering
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) return;
    initSidebar();
    loadAlerts();

    // Severity filter
    const severityFilter = document.getElementById('severity-filter');
    if (severityFilter) {
        severityFilter.addEventListener('change', () => loadAlerts());
    }

    // Read status filter
    const readFilter = document.getElementById('read-filter');
    if (readFilter) {
        readFilter.addEventListener('change', () => loadAlerts());
    }
});


// ============================================================
// Load Alerts
// ============================================================

async function loadAlerts() {
    const severity = document.getElementById('severity-filter')?.value || '';
    const is_read = document.getElementById('read-filter')?.value;

    const params = { limit: 100 };
    if (severity) params.severity = severity;
    if (is_read !== '' && is_read !== undefined) params.is_read = is_read;

    const result = await api.getAlerts(params);

    if (result && result.status === 'success') {
        renderAlerts(result.alerts);
        document.getElementById('alert-total').textContent = result.alerts.length;

        const unreadCount = result.alerts.filter(a => !a.is_read).length;
        document.getElementById('alert-unread').textContent = unreadCount;
    }
}

function renderAlerts(alerts) {
    const container = document.getElementById('alerts-list');
    if (!container) return;

    if (alerts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔔</div>
                <h3>No Alerts</h3>
                <p>All clear! No alerts match your filter criteria.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = alerts.map(alert => `
        <div class="alert-item ${!alert.is_read ? 'unread' : ''} ${alert.severity === 'critical' ? 'critical' : ''}"
             id="alert-${alert.id}"
             onclick="markAsRead(${alert.id})">
            <div class="alert-icon" style="background: ${getAlertIconBg(alert.severity)}; color: ${getAlertIconColor(alert.severity)}">
                ${getAlertEmoji(alert.severity)}
            </div>
            <div class="alert-content">
                <div class="flex-between">
                    <div class="alert-title">
                        ${alert.consumer_name || 'Unknown Consumer'}
                        <span class="text-muted" style="font-weight:400; font-size:11px">${alert.cons_no || ''}</span>
                    </div>
                    ${getSeverityBadge(alert.severity)}
                </div>
                <div class="alert-message">${alert.message}</div>
                <div class="alert-time flex" style="gap:16px">
                    <span>📅 ${formatDateTime(alert.created_at)}</span>
                    ${alert.area ? `<span>📍 ${alert.area}</span>` : ''}
                    ${alert.difference ? `<span>⚡ Δ ${alert.difference}A</span>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

function getAlertIconBg(severity) {
    const map = {
        critical: 'var(--color-danger-bg)',
        warning: 'var(--color-warning-bg)',
        info: 'var(--color-info-bg)'
    };
    return map[severity] || map.info;
}

function getAlertIconColor(severity) {
    const map = {
        critical: 'var(--color-danger)',
        warning: 'var(--color-warning)',
        info: 'var(--color-info)'
    };
    return map[severity] || map.info;
}

function getAlertEmoji(severity) {
    const map = {
        critical: '🚨',
        warning: '⚡',
        info: 'ℹ️'
    };
    return map[severity] || '🔔';
}


// ============================================================
// Mark Alert as Read
// ============================================================

async function markAsRead(alertId) {
    const result = await api.markAlertRead(alertId);

    if (result && result.status === 'success') {
        const alertEl = document.getElementById(`alert-${alertId}`);
        if (alertEl) {
            alertEl.classList.remove('unread');
        }
        updateAlertBadge();
    }
}

async function markAllRead() {
    const result = await api.markAllAlertsRead();

    if (result && result.status === 'success') {
        showToast(result.message, 'success');
        loadAlerts();
        updateAlertBadge();
    }
}
