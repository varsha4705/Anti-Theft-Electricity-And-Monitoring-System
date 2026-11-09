/**
 * Shared Application Utilities — Navigation, Toast, Auth Guard
 */

// ============================================================
// Auth Guard — Redirect to login if not authenticated
// ============================================================

function checkAuth() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
        window.location.href = '/';
        return false;
    }
    return true;
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem('user'));
    } catch {
        return null;
    }
}

function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    window.location.href = '/';
}


// ============================================================
// Toast Notifications
// ============================================================

function showToast(message, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-text">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-out');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}


// ============================================================
// Sidebar Navigation
// ============================================================

function initSidebar() {
    const user = getUser();
    const currentPage = window.location.pathname.split('/').pop() || 'dashboard.html';

    // Set user info
    const userNameEl = document.getElementById('sidebar-user-name');
    const userRoleEl = document.getElementById('sidebar-user-role');
    const userAvatarEl = document.getElementById('sidebar-user-avatar');

    if (user && userNameEl) {
        userNameEl.textContent = user.full_name || user.username;
        userRoleEl.textContent = user.role || 'Admin';
        userAvatarEl.textContent = (user.full_name || user.username || 'A').charAt(0).toUpperCase();
    }

    // Set active nav link
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPage || (currentPage === '' && href === 'dashboard.html')) {
            link.classList.add('active');
        }
    });

    // Mobile toggle
    const mobileToggle = document.getElementById('mobile-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }

    // Update alert badge
    updateAlertBadge();
}

async function updateAlertBadge() {
    try {
        const result = await api.getAlertCount();
        if (result && result.status === 'success') {
            const badge = document.getElementById('alert-badge');
            if (badge) {
                if (result.unread > 0) {
                    badge.textContent = result.unread > 99 ? '99+' : result.unread;
                    badge.classList.remove('hidden');
                } else {
                    badge.classList.add('hidden');
                }
            }
        }
    } catch (e) {
        // Silently fail
    }
}


// ============================================================
// Modal Utilities
// ============================================================

function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(m => {
        m.classList.remove('active');
    });
    document.body.style.overflow = '';
}

// Close modals on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        closeAllModals();
    }
});

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeAllModals();
    }
});


// ============================================================
// Utility Formatters
// ============================================================

function formatDateTime(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
    });
}

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return formatDate(dateStr);
}

function getStatusBadge(status) {
    const badges = {
        normal: '<span class="badge badge-success badge-dot">Normal</span>',
        suspicious: '<span class="badge badge-danger badge-dot">Suspicious</span>',
        flagged: '<span class="badge badge-warning badge-dot">Flagged</span>'
    };
    return badges[status] || badges.normal;
}

function getSeverityBadge(severity) {
    const badges = {
        critical: '<span class="badge badge-danger">⚠ Critical</span>',
        warning: '<span class="badge badge-warning">⚡ Warning</span>',
        info: '<span class="badge badge-info">ℹ Info</span>'
    };
    return badges[severity] || badges.info;
}

function animateCounter(element, target, duration = 1000) {
    const start = parseInt(element.textContent) || 0;
    const range = target - start;
    const startTime = performance.now();

    function step(timestamp) {
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        element.textContent = Math.round(start + range * eased);
        if (progress < 1) {
            requestAnimationFrame(step);
        }
    }
    requestAnimationFrame(step);
}


// ============================================================
// Sidebar HTML Template
// ============================================================

function getSidebarHTML() {
    return `
    <aside class="sidebar" id="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-brand">
                <div class="brand-icon">⚡</div>
                <div class="brand-text">
                    <h2>Anti-Theft EMS</h2>
                    <span>Monitoring System</span>
                </div>
            </div>
        </div>

        <nav class="sidebar-nav">
            <div class="nav-section">
                <div class="nav-section-title">Main</div>
                <a href="dashboard.html" class="nav-link" id="nav-dashboard">
                    <span class="nav-icon">📊</span>
                    Dashboard
                </a>
                <a href="monitor.html" class="nav-link" id="nav-monitor">
                    <span class="nav-icon">📡</span>
                    Live Monitor
                </a>
            </div>

            <div class="nav-section">
                <div class="nav-section-title">Management</div>
                <a href="consumers.html" class="nav-link" id="nav-consumers">
                    <span class="nav-icon">👥</span>
                    Consumers
                </a>
                <a href="predictions.html" class="nav-link" id="nav-predictions">
                    <span class="nav-icon">🤖</span>
                    Predictions
                </a>
                <a href="alerts.html" class="nav-link" id="nav-alerts">
                    <span class="nav-icon">🔔</span>
                    Alerts
                    <span class="nav-badge hidden" id="alert-badge">0</span>
                </a>
            </div>
        </nav>

        <div class="sidebar-footer">
            <div class="sidebar-user" id="logout-btn" title="Click to logout">
                <div class="user-avatar" id="sidebar-user-avatar">A</div>
                <div class="user-info">
                    <h4 id="sidebar-user-name">Admin</h4>
                    <span id="sidebar-user-role">Admin</span>
                </div>
            </div>
        </div>
    </aside>
    `;
}
