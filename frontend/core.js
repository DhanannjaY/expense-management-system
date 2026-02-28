/**
 * Core Application Module - OPTIMIZED VERSION - FIXED
 * Django REST Framework Token Authentication
 */

// ================= CONFIG =================
const CONFIG = {
    API_URL: 'http://localhost:8000/api',
    CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
    MAX_RETRIES: 3,
    RETRY_DELAY: 1000,
    REQUEST_TIMEOUT: 30000, // 30 seconds
    MAX_CACHE_SIZE: 50 // Maximum number of cached items
};

// ================= AUTH MANAGER =================
class AuthManager {
    constructor() {
        this.token = this.getToken();
        this.user = this.getUser();
        this._authCheckPromise = null; // Cache auth check promise
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
        try {
            return raw ? JSON.parse(raw) : null;
        } catch (e) {
            console.warn('Failed to parse user data:', e);
            return null;
        }
    }

    setUser(user, remember = false) {
        const storage = remember ? localStorage : sessionStorage;
        storage.setItem('user', JSON.stringify(user));
        this.user = user;
    }

    async login(username, password, remember = false) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);

            const response = await fetch(`${CONFIG.API_URL}/auth/login/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Login failed');
            }

            this.setToken(data.token, remember);
            this.setUser(data.user, remember);
            this._authCheckPromise = null; // Reset auth check cache

            return { success: true, user: data.user };
        } catch (error) {
            if (error.name === 'AbortError') {
                return { success: false, error: 'Request timeout - please try again' };
            }
            return { success: false, error: error.message };
        }
    }

    async logout() {
        try {
            if (this.token) {
                // Don't wait for logout response
                fetch(`${CONFIG.API_URL}/auth/logout/`, {
                    method: 'POST',
                    headers: this.getHeaders(),
                    keepalive: true // Ensures request completes even if page unloads
                }).catch(() => {}); // Ignore errors
            }
        } finally {
            this.clearAuthData();
            window.location.href = 'index.html';
        }
    }

    clearAuthData() {
        sessionStorage.clear();
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        this.token = null;
        this.user = null;
        this._authCheckPromise = null;
    }

    async checkAuth() {
        // Return cached promise if already checking
        if (this._authCheckPromise) {
            return this._authCheckPromise;
        }

        if (!this.token) {
            return false;
        }

        this._authCheckPromise = (async () => {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000);

                const response = await fetch(`${CONFIG.API_URL}/auth/verify/`, {
                    headers: this.getHeaders(),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!response.ok) throw new Error('Auth check failed');

                const data = await response.json();
                if (data.authenticated) {
                    this.user = data.user;
                    return true;
                }
                return false;
            } catch (error) {
                console.warn('Auth verification failed:', error);
                this.clearAuthData();
                return false;
            } finally {
                // Clear promise cache after 5 seconds
                setTimeout(() => {
                    this._authCheckPromise = null;
                }, 5000);
            }
        })();

        return this._authCheckPromise;
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
        this.accessCount = new Map(); // Track access frequency
    }

    set(key, data, duration = CONFIG.CACHE_DURATION) {
        // Implement LRU eviction if cache is full
        if (this.cache.size >= CONFIG.MAX_CACHE_SIZE) {
            this.evictLRU();
        }

        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            duration
        });
        this.accessCount.set(key, 0);
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        // Check expiration
        if (Date.now() - item.timestamp > item.duration) {
            this.cache.delete(key);
            this.accessCount.delete(key);
            return null;
        }

        // Update access count for LRU
        this.accessCount.set(key, (this.accessCount.get(key) || 0) + 1);
        return item.data;
    }

    evictLRU() {
        // Find least recently used item
        let lruKey = null;
        let minAccess = Infinity;

        for (const [key, count] of this.accessCount.entries()) {
            if (count < minAccess) {
                minAccess = count;
                lruKey = key;
            }
        }

        if (lruKey) {
            this.cache.delete(lruKey);
            this.accessCount.delete(lruKey);
        }
    }

    clear(key) {
        if (key) {
            this.cache.delete(key);
            this.accessCount.delete(key);
        } else {
            this.cache.clear();
            this.accessCount.clear();
        }
    }

    clearAll() {
        this.cache.clear();
        this.accessCount.clear();
    }

    getStats() {
        return {
            size: this.cache.size,
            maxSize: CONFIG.MAX_CACHE_SIZE,
            items: Array.from(this.cache.keys())
        };
    }
}

// ================= API MANAGER =================
class APIManager {
    constructor(auth, cache) {
        this.auth = auth;
        this.cache = cache;
        this.pendingRequests = new Map(); // Deduplicate simultaneous requests
    }

    async request(url, options = {}, retries = CONFIG.MAX_RETRIES) {
        const fullUrl = `${CONFIG.API_URL}${url}`;
        const requestKey = `${options.method || 'GET'}:${url}`;

        // Deduplicate simultaneous identical requests
        if (this.pendingRequests.has(requestKey)) {
            return this.pendingRequests.get(requestKey);
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT);

        const requestPromise = (async () => {
            try {
                const response = await fetch(fullUrl, {
                    ...options,
                    headers: {
                        ...this.auth.getHeaders(),
                        ...options.headers
                    },
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                // Handle 401 Unauthorized
                if (response.status === 401) {
                    await this.auth.logout();
                    throw new Error('Session expired');
                }

                // Handle other error statuses
                if (!response.ok) {
                    const contentType = response.headers.get('content-type');
                    let errorMessage = `HTTP ${response.status}`;

                    if (contentType?.includes('application/json')) {
                        const err = await response.json().catch(() => ({}));
                        errorMessage = err.detail || err.error || err.message || errorMessage;
                    }

                    throw new Error(errorMessage);
                }

                return await response.json();

            } catch (error) {
                clearTimeout(timeoutId);

                // Handle timeout
                if (error.name === 'AbortError') {
                    throw new Error('Request timeout - please try again');
                }

                // Retry on network errors
                if (retries > 0 && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
                    await this.delay(CONFIG.RETRY_DELAY);
                    return this.request(url, options, retries - 1);
                }

                throw error;
            } finally {
                this.pendingRequests.delete(requestKey);
            }
        })();

        this.pendingRequests.set(requestKey, requestPromise);
        return requestPromise;
    }

    async get(url, useCache = true) {
        const key = `GET:${url}:${this.auth.user?.id || 'anon'}`;

        if (useCache) {
            const cached = this.cache.get(key);
            if (cached) {
                console.debug('Cache hit:', key);
                return cached;
            }
        }

        const data = await this.request(url);
        if (useCache) this.cache.set(key, data);
        return data;
    }

    post(url, body) {
        this.cache.clearAll(); // Clear all cache on mutations
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

    patch(url, body) {
        this.cache.clearAll();
        return this.request(url, {
            method: 'PATCH',
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
        // More comprehensive XSS protection
        return input
            .trim()
            .replace(/[<>'"]/g, '') // Remove potentially dangerous characters
            .substring(0, 10000); // Limit length
    }

    static validateExpense(expense) {
        const errors = [];

        if (!expense.title || expense.title.trim().length < 1) {
            errors.push('Title is required');
        } else if (expense.title.length > 200) {
            errors.push('Title must be less than 200 characters');
        }

        const amount = parseFloat(expense.amount);
        if (!expense.amount || isNaN(amount) || amount <= 0) {
            errors.push('Amount must be greater than 0');
        } else if (amount > 10000000) {
            errors.push('Amount seems unreasonably high');
        }

        if (!expense.category) {
            errors.push('Category is required');
        }

        if (!expense.date) {
            errors.push('Date is required');
        } else {
            const expenseDate = new Date(expense.date);
            const today = new Date();
            today.setHours(23, 59, 59, 999);
            
            if (expenseDate > today) {
                errors.push('Date cannot be in the future');
            }
            
            if (expenseDate.getFullYear() < 1900) {
                errors.push('Date seems unreasonably old');
            }
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

        const amount = parseFloat(budget.amount);
        if (!budget.amount || isNaN(amount) || amount <= 0) {
            errors.push('Budget amount must be greater than 0');
        } else if (amount > 100000000) {
            errors.push('Budget amount seems unreasonably high');
        }

        if (!budget.period) {
            errors.push('Period is required');
        } else if (!['weekly', 'monthly', 'yearly'].includes(budget.period)) {
            errors.push('Invalid period selected');
        }

        return {
            isValid: errors.length === 0,
            errors
        };
    }

    static validateEmail(email) {
        const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return emailRegex.test(email);
    }

    static validatePassword(password) {
        return password && password.length >= 6;
    }
}

// ================= UI HELPERS =================
class NotificationManager {
    static notifications = [];
    static maxNotifications = 3;

    static show(msg, type = 'info', duration = 5000) {
        // Limit number of simultaneous notifications
        if (this.notifications.length >= this.maxNotifications) {
            const oldest = this.notifications.shift();
            oldest?.remove();
        }

        const el = document.createElement('div');
        el.className = `alert alert-${type} app-notification alert-dismissible fade show`;
        el.style.cssText = `
            position: fixed;
            top: ${20 + (this.notifications.length * 70)}px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 500px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            animation: slideIn 0.3s ease-out;
        `;
        el.innerHTML = `
            <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            ${msg}
        `;

        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(400px); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        if (!document.querySelector('style[data-notifications]')) {
            style.setAttribute('data-notifications', 'true');
            document.head.appendChild(style);
        }

        document.body.appendChild(el);
        this.notifications.push(el);

        // Remove from array when closed
        el.addEventListener('close.bs.alert', () => {
            const index = this.notifications.indexOf(el);
            if (index > -1) this.notifications.splice(index, 1);
        });

        if (duration) {
            setTimeout(() => {
                if (el.parentElement) {
                    el.classList.remove('show');
                    setTimeout(() => el.remove(), 150);
                }
            }, duration);
        }
    }

    static success(m) { this.show(m, 'success'); }
    static error(m) { this.show(m, 'danger', 7000); }
    static warning(m) { this.show(m, 'warning', 6000); }
    static info(m) { this.show(m, 'info'); }
}

class LoadingManager {
    static showButton(btn, loading = true) {
        if (!btn) return;
        
        if (loading) {
            btn.disabled = true;
            if (!btn.dataset.text) {
                btn.dataset.text = btn.innerHTML;
            }
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
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">${message}</span>
                    </div>
                    <p class="mt-2 text-muted">${message}</p>
                </div>
            `;
        }
    }

    static hide(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
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

        // Don't show notification for session expired (handled by redirect)
        if (message !== 'Session expired') {
            NotificationManager.error(message);
        }

        // Log to external service in production (example)
        if (window.location.hostname !== 'localhost') {
            // this.logToService(error, context);
        }
    }

    static logToService(error, context) {
        // Example: Send to error tracking service
        // fetch('/api/log-error', {
        //     method: 'POST',
        //     body: JSON.stringify({ error: error.message, context })
        // });
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
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        
        // Cleanup
        setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }, 100);
    }

    static debounce(func, wait = 300) {
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

    static throttle(func, limit = 300) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    static copyToClipboard(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text);
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                document.body.removeChild(textArea);
                return Promise.resolve();
            } catch (err) {
                document.body.removeChild(textArea);
                return Promise.reject(err);
            }
        }
    }
}

// ================= INIT =================
const auth = new AuthManager();
const cache = new CacheManager();
const api = new APIManager(auth, cache);

// ================= CATEGORY LOADER =================
const CategoryLoader = {
    _cache: null,

    async load(selectIds = [], defaultLabel = 'Select Category') {
        try {
            if (!this._cache) {
                const data = await api.get('/categories/');
                this._cache = data.results || data;
            }
            selectIds.forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                el.innerHTML = `<option value="">${defaultLabel}</option>` +
                    this._cache.map(c =>
                        `<option value="${c.id}">${Utils.escapeHtml(c.name)}</option>`
                    ).join('');
            });
            return this._cache;
        } catch (err) {
            ErrorHandler.handle(err, 'Load Categories');
            return [];
        }
    },

    clearCache() { this._cache = null; }
};

window.AppCore = {
    auth,
    cache,
    api,
    ValidationManager,
    NotificationManager,
    LoadingManager,
    ErrorHandler,
    Utils,
    CONFIG,
    CategoryLoader
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

// ================= PERFORMANCE MONITORING =================
if (window.performance && window.performance.mark) {
    window.performance.mark('appcore-loaded');
}

// ================= CLEANUP =================
window.addEventListener('beforeunload', () => {
    cache.clearAll();
});

// ================= READY =================
console.log('✅ AppCore initialized successfully');
console.log('Cache stats:', cache.getStats());