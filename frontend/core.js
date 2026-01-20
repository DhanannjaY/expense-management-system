/**
 * Core Application Module - FINAL FIX
 * Django REST Framework Token Authentication
 */

// ================= CONFIG =================
const CONFIG = {
    API_URL: 'http://localhost:8000/api',
    CACHE_DURATION: 5 * 60 * 1000,
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000
};

// ================= AUTH MANAGER =================
class AuthManager {
    constructor() {
        this.token = this.getToken();
        this.user = this.getUser();
    }

    getToken() {
        return sessionStorage.getItem('auth_token') || localStorage.getItem('auth_token');
    }

    setToken(token, remember = false) {
        const storage = remember ? localStorage : sessionStorage;
        storage.setItem('auth_token', token);
        this.token = token;
    }

    getUser() {
        const raw = sessionStorage.getItem('user') || localStorage.getItem('user');
        return raw ? JSON.parse(raw) : null;
    }

    setUser(user, remember = false) {
        const storage = remember ? localStorage : sessionStorage;
        storage.setItem('user', JSON.stringify(user));
        this.user = user;
    }

    async login(username, password, remember = false) {
        try {
            const response = await fetch(`${CONFIG.API_URL}/auth/login/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Login failed');
            }

            this.setToken(data.token, remember);
            this.setUser(data.user, remember);

            return { success: true, user: data.user };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    async logout() {
        try {
            if (this.token) {
                await fetch(`${CONFIG.API_URL}/auth/logout/`, {
                    method: 'POST',
                    headers: this.getHeaders()
                });
            }
        } catch (e) {
            console.warn('Logout request failed');
        } finally {
            sessionStorage.clear();
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            this.token = null;
            this.user = null;
            window.location.href = 'index.html';
        }
    }

    async checkAuth() {
        if (!this.token) return false;

        try {
            const response = await fetch(`${CONFIG.API_URL}/auth/verify/`, {
                headers: this.getHeaders()
            });

            if (!response.ok) throw new Error();

            const data = await response.json();
            if (data.authenticated) {
                this.user = data.user;
                return true;
            }
            return false;
        } catch {
            await this.logout();
            return false;
        }
    }

    isAuthenticated() {
        return !!this.token;
    }

    getHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Token ${this.token}`;
        }
        return headers;
    }
}

// ================= CACHE MANAGER =================
class CacheManager {
    constructor() {
        this.cache = new Map();
    }

    set(key, data, duration = CONFIG.CACHE_DURATION) {
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            duration
        });
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        if (Date.now() - item.timestamp > item.duration) {
            this.cache.delete(key);
            return null;
        }
        return item.data;
    }

    clear(key) {
        key ? this.cache.delete(key) : this.cache.clear();
    }

    clearAll() {
        this.cache.clear();
    }
}

// ================= API MANAGER =================
class APIManager {
    constructor(auth, cache) {
        this.auth = auth;
        this.cache = cache;
    }

    async request(url, options = {}, retries = CONFIG.MAX_RETRIES) {
        const fullUrl = `${CONFIG.API_URL}${url}`;

        try {
            const response = await fetch(fullUrl, {
                ...options,
                headers: {
                    ...this.auth.getHeaders(),
                    ...options.headers
                }
            });

            if (response.status === 401) {
                await this.auth.logout();
                throw new Error('Session expired');
            }

            if (!response.ok) {
                const err = await response.json().catch(() => ({}));
                throw new Error(
                    err.detail || err.error || err.message || `HTTP ${response.status}`
                );
            }

            return await response.json();
        } catch (error) {
            if (retries > 0 && error.message.includes('Failed to fetch')) {
                await this.delay(CONFIG.RETRY_DELAY);
                return this.request(url, options, retries - 1);
            }
            throw error;
        }
    }

    async get(url, useCache = true) {
        const key = `GET:${url}:${this.auth.user?.id || 'anon'}`;

        if (useCache) {
            const cached = this.cache.get(key);
            if (cached) return cached;
        }

        const data = await this.request(url);
        if (useCache) this.cache.set(key, data);
        return data;
    }

    post(url, body) {
        this.cache.clearAll();
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    put(url, body) {
        this.cache.clearAll();
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    }

    delete(url) {
        this.cache.clearAll();
        return this.request(url, { method: 'DELETE' });
    }

    delay(ms) {
        return new Promise(res => setTimeout(res, ms));
    }
}

// ================= VALIDATION MANAGER =================
class ValidationManager {
    static sanitizeInput(input) {
        if (typeof input !== 'string') return input;
        return input.trim().replace(/[<>]/g, '');
    }

    static validateExpense(expense) {
        const errors = [];

        if (!expense.title || expense.title.trim().length < 1) {
            errors.push('Title is required');
        }
        if (!expense.amount || parseFloat(expense.amount) <= 0) {
            errors.push('Amount must be greater than 0');
        }
        if (!expense.category) {
            errors.push('Category is required');
        }
        if (!expense.date) {
            errors.push('Date is required');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    static validateBudget(budget) {
        const errors = [];

        if (!budget.category) {
            errors.push('Category is required');
        }
        if (!budget.amount || parseFloat(budget.amount) <= 0) {
            errors.push('Budget amount must be greater than 0');
        }
        if (!budget.period) {
            errors.push('Period is required');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }
}

// ================= UI HELPERS =================
class NotificationManager {
    static show(msg, type = 'info', duration = 5000) {
        document.querySelectorAll('.app-notification').forEach(n => n.remove());

        const el = document.createElement('div');
        el.className = `alert alert-${type} app-notification`;
        el.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;
        el.innerHTML = `
            <button type="button" class="btn-close float-end" onclick="this.parentElement.remove()"></button>
            ${msg}
        `;
        document.body.appendChild(el);

        if (duration) {
            setTimeout(() => el.remove(), duration);
        }
    }

    static success(m) { this.show(m, 'success'); }
    static error(m) { this.show(m, 'danger', 7000); }
    static warning(m) { this.show(m, 'warning'); }
    static info(m) { this.show(m, 'info'); }
}

class LoadingManager {
    static showButton(btn, loading = true) {
        if (!btn) return;
        
        if (loading) {
            btn.disabled = true;
            btn.dataset.text = btn.innerHTML;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Processing...`;
        } else {
            btn.disabled = false;
            btn.innerHTML = btn.dataset.text || 'Submit';
        }
    }

    static show(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary" role="status"></div>
                    <p class="mt-2 text-muted">${message}</p>
                </div>
            `;
        }
    }
}

class ErrorHandler {
    static handle(error, context = '') {
        console.error(`Error [${context}]:`, error);
        
        let message = 'An unexpected error occurred';
        
        if (error.message) {
            message = error.message;
        }
        
        NotificationManager.error(message);
    }
}

class Utils {
    static formatCurrency(amount, symbol = 'Rs.') {
        const num = parseFloat(amount) || 0;
        return `${symbol}${num.toLocaleString('en-NP', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 2
        })}`;
    }

    static formatDate(dateString, format = 'short') {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        if (isNaN(date.getTime())) return 'Invalid Date';

        const options = format === 'full' 
            ? { year: 'numeric', month: 'short', day: 'numeric' }
            : { month: 'short', day: 'numeric' };

        return date.toLocaleDateString('en-US', options);
    }

    static escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// ================= INIT =================
const auth = new AuthManager();
const cache = new CacheManager();
const api = new APIManager(auth, cache);

window.AppCore = {
    auth,
    cache,
    api,
    ValidationManager,
    NotificationManager,
    LoadingManager,
    ErrorHandler,
    Utils,
    CONFIG
};

// ================= PAGE GUARD =================
window.requireAuth = async function () {
    if (!auth.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    const valid = await auth.checkAuth();
    if (!valid) {
        window.location.href = 'login.html';
    }
};

// ================= CLEANUP =================
window.addEventListener('beforeunload', () => {
    cache.clearAll();
});

console.log('✓ AppCore initialized successfully');