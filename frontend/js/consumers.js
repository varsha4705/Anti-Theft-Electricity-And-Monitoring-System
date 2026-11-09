/**
 * Consumer Management — CRUD operations & table
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) return;
    initSidebar();
    loadConsumers();

    // Search
    const searchInput = document.getElementById('consumer-search');
    if (searchInput) {
        let debounce;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(() => loadConsumers(), 300);
        });
    }

    // Filter by status
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', () => loadConsumers());
    }

    // Add consumer form
    const addForm = document.getElementById('add-consumer-form');
    if (addForm) {
        addForm.addEventListener('submit', handleAddConsumer);
    }

    // Edit consumer form
    const editForm = document.getElementById('edit-consumer-form');
    if (editForm) {
        editForm.addEventListener('submit', handleEditConsumer);
    }
});


// ============================================================
// Load Consumers
// ============================================================

async function loadConsumers() {
    const search = document.getElementById('consumer-search')?.value || '';
    const status = document.getElementById('status-filter')?.value || '';

    const result = await api.getConsumers({ search, status });

    if (result && result.status === 'success') {
        renderConsumerTable(result.consumers);
        document.getElementById('consumer-count').textContent = result.consumers.length;
    }
}

function renderConsumerTable(consumers) {
    const tbody = document.getElementById('consumers-tbody');
    if (!tbody) return;

    if (consumers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted" style="padding:40px">
                    No consumers found
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = consumers.map(c => `
        <tr>
            <td class="td-mono td-bold">${c.cons_no}</td>
            <td class="td-bold">${c.name}</td>
            <td>${c.area || '—'}</td>
            <td class="td-mono">${c.meter_id || '—'}</td>
            <td>${c.phone || '—'}</td>
            <td>${getStatusBadge(c.status)}</td>
            <td>
                <div style="display:flex; gap:6px;">
                    <button class="btn btn-secondary btn-sm" onclick="openEditModal(${c.id})" title="Edit">✏️</button>
                    <button class="btn btn-danger btn-sm" onclick="confirmDelete(${c.id}, '${c.name}')" title="Delete">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');
}


// ============================================================
// Add Consumer
// ============================================================

function openAddModal() {
    document.getElementById('add-consumer-form').reset();
    openModal('add-consumer-modal');
}

async function handleAddConsumer(e) {
    e.preventDefault();

    const data = {
        cons_no: document.getElementById('add-cons-no').value.trim(),
        name: document.getElementById('add-name').value.trim(),
        area: document.getElementById('add-area').value.trim(),
        address: document.getElementById('add-address').value.trim(),
        meter_id: document.getElementById('add-meter-id').value.trim(),
        phone: document.getElementById('add-phone').value.trim()
    };

    if (!data.cons_no || !data.name) {
        showToast('Consumer No and Name are required', 'warning');
        return;
    }

    const result = await api.addConsumer(data);

    if (result && result.status === 'success') {
        showToast('Consumer added successfully!', 'success');
        closeModal('add-consumer-modal');
        loadConsumers();
    } else {
        showToast(result?.message || 'Failed to add consumer', 'error');
    }
}


// ============================================================
// Edit Consumer
// ============================================================

let editingConsumerId = null;

async function openEditModal(id) {
    const result = await api.getConsumer(id);

    if (result && result.status === 'success') {
        const c = result.consumer;
        editingConsumerId = c.id;

        document.getElementById('edit-name').value = c.name || '';
        document.getElementById('edit-area').value = c.area || '';
        document.getElementById('edit-address').value = c.address || '';
        document.getElementById('edit-meter-id').value = c.meter_id || '';
        document.getElementById('edit-phone').value = c.phone || '';
        document.getElementById('edit-status').value = c.status || 'normal';

        openModal('edit-consumer-modal');
    }
}

async function handleEditConsumer(e) {
    e.preventDefault();

    const data = {
        name: document.getElementById('edit-name').value.trim(),
        area: document.getElementById('edit-area').value.trim(),
        address: document.getElementById('edit-address').value.trim(),
        meter_id: document.getElementById('edit-meter-id').value.trim(),
        phone: document.getElementById('edit-phone').value.trim(),
        status: document.getElementById('edit-status').value
    };

    const result = await api.updateConsumer(editingConsumerId, data);

    if (result && result.status === 'success') {
        showToast('Consumer updated!', 'success');
        closeModal('edit-consumer-modal');
        loadConsumers();
    } else {
        showToast(result?.message || 'Update failed', 'error');
    }
}


// ============================================================
// Delete Consumer
// ============================================================

async function confirmDelete(id, name) {
    if (confirm(`Are you sure you want to delete "${name}"? This will also delete all their sensor readings and alerts.`)) {
        const result = await api.deleteConsumer(id);

        if (result && result.status === 'success') {
            showToast('Consumer deleted', 'success');
            loadConsumers();
        } else {
            showToast(result?.message || 'Delete failed', 'error');
        }
    }
}
