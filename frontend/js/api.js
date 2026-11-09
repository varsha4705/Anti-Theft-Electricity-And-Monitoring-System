/**
 * API Client — Handles all HTTP requests to the Flask backend.
 */

const API_BASE = '/api';

class ApiClient {
    constructor() {
        this.baseUrl = API_BASE;
    }

    /**
     * Get the JWT token from localStorage.
     */
    getToken() {
        return localStorage.getItem('auth_token');
    }

    /**
     * Build headers with optional auth token.
     */
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (includeAuth) {
            const token = this.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        return headers;
    }

    /**
     * Make an HTTP request.
     */
    async request(method, endpoint, data = null, includeAuth = true) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: this.getHeaders(includeAuth)
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);

            if (response.status === 401 && endpoint !== '/auth/login') {
                // Token expired or invalid
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user');
                window.location.href = '/';
                return null;
            }

            const result = await response.json();
            return result;
        } catch (error) {
            console.error(`API Error [${method} ${endpoint}]:`, error);
            return {
                status: 'error',
                message: 'Network error. Please check your connection.'
            };
        }
    }

    /**
     * Upload file via multipart form data.
     */
    async upload(endpoint, formData) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = this.getToken();
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers,
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error(`Upload Error:`, error);
            return {
                status: 'error',
                message: 'Upload failed. Please try again.'
            };
        }
    }

    // ========== AUTH ==========
    async login(username, password) {
        return this.request('POST', '/auth/login', { username, password }, false);
    }

    async register(data) {
        return this.request('POST', '/auth/register', data, false);
    }

    async getProfile() {
        return this.request('GET', '/auth/profile');
    }

    // ========== DASHBOARD ==========
    async getDashboardStats() {
        return this.request('GET', '/dashboard/stats');
    }

    async getChartData() {
        return this.request('GET', '/dashboard/chart-data');
    }

    // ========== CONSUMERS ==========
    async getConsumers(params = {}) {
        let query = '';
        const queryParts = [];
        if (params.area) queryParts.push(`area=${encodeURIComponent(params.area)}`);
        if (params.status) queryParts.push(`status=${encodeURIComponent(params.status)}`);
        if (params.search) queryParts.push(`search=${encodeURIComponent(params.search)}`);
        if (queryParts.length) query = '?' + queryParts.join('&');
        return this.request('GET', `/consumers${query}`);
    }

    async getConsumer(id) {
        return this.request('GET', `/consumers/${id}`);
    }

    async addConsumer(data) {
        return this.request('POST', '/consumers', data);
    }

    async updateConsumer(id, data) {
        return this.request('PUT', `/consumers/${id}`, data);
    }

    async deleteConsumer(id) {
        return this.request('DELETE', `/consumers/${id}`);
    }

    // ========== SENSOR ==========
    async getLiveData() {
        return this.request('GET', '/sensor/live');
    }

    async getSensorReadings(consumerId, limit = 100) {
        return this.request('GET', `/sensor/readings/${consumerId}?limit=${limit}`);
    }

    // ========== PREDICTIONS ==========
    async predictSingle(data) {
        return this.request('POST', '/predict/single', data);
    }

    async predictBatch(formData) {
        return this.upload('/predict/batch', formData);
    }

    async getPredictionHistory(limit = 50) {
        return this.request('GET', `/predict/history?limit=${limit}`);
    }

    // ========== ALERTS ==========
    async getAlerts(params = {}) {
        let query = '';
        const queryParts = [];
        if (params.severity) queryParts.push(`severity=${params.severity}`);
        if (params.is_read !== undefined) queryParts.push(`is_read=${params.is_read}`);
        if (params.limit) queryParts.push(`limit=${params.limit}`);
        if (queryParts.length) query = '?' + queryParts.join('&');
        return this.request('GET', `/alerts${query}`);
    }

    async markAlertRead(id) {
        return this.request('PUT', `/alerts/${id}/read`);
    }

    async markAllAlertsRead() {
        return this.request('PUT', '/alerts/read-all');
    }

    async getAlertCount() {
        return this.request('GET', '/alerts/count');
    }
}

// Singleton instance
const api = new ApiClient();
