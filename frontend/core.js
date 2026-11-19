const CONFIG = {
  API_URL: 'http://localhost:8000/api',
  CACHE_TTL: 3 * 60 * 1000,
  TIMEOUT: 20000,
  MAX_RETRIES: 2,
  RETRY_DELAY: 800,
};

const CURRENCY_SYMBOLS = {
  NPR: 'Rs.',
  USD: '$',
  EUR: '€',
  INR: '₹',
  GBP: '£',
};

/* ── Resolve login.html path relative to current page location ── */
function loginPath() {
  const parts = window.location.pathname.split('/');
  parts[parts.length - 1] = 'login.html';
  return parts.join('/');
}

/* ──────────────── THEME MANAGER ──────────────── */
const ThemeManager = {
  STORAGE_KEY: 'ems_theme',

  get() {
    return localStorage.getItem(this.STORAGE_KEY) || 'system';
  },

  apply(theme) {
    const mode = theme || this.get();
    localStorage.setItem(this.STORAGE_KEY, mode);
    if (mode === 'light' || mode === 'dark') {
      document.documentElement.setAttribute('data-theme', mode);
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  },
};

// Apply saved theme immediately before first paint
ThemeManager.apply();

/* ──────────────── AUTH MANAGER ──────────────── */
class AuthManager {
  constructor() {
    this.token = sessionStorage.getItem('ems_token') || localStorage.getItem('ems_token');
    this.user  = this._parseUser();
    if (this.user?.theme) ThemeManager.apply(this.user.theme);
  }

  _parseUser() {
    try {
      const raw = sessionStorage.getItem('ems_user') || localStorage.getItem('ems_user');
      return raw ? JSON.parse(raw) : null;
    } catch { return null; }
  }

  setSession(token, user, remember = false) {
    const store = remember ? localStorage : sessionStorage;
    store.setItem('ems_token', token);
    store.setItem('ems_user', JSON.stringify(user));
    this.token = token;
    this.user  = user;
    if (user?.theme) ThemeManager.apply(user.theme);
  }

  updateStoredUser(partial) {
    if (!this.user) return;
    this.user = { ...this.user, ...partial };
    const serialized = JSON.stringify(this.user);
    if (localStorage.getItem('ems_user')) localStorage.setItem('ems_user', serialized);
    if (sessionStorage.getItem('ems_user')) sessionStorage.setItem('ems_user', serialized);
    if (partial.theme) ThemeManager.apply(partial.theme);
  }

  clear() {
    ['ems_token', 'ems_user'].forEach(k => {
      sessionStorage.removeItem(k);
      localStorage.removeItem(k);
    });
    this.token = null;
    this.user  = null;
  }

  isAuthenticated() { return !!this.token; }

  getHeaders() {
    const h = { 'Content-Type': 'application/json' };
    if (this.token) h['Authorization'] = `Token ${this.token}`;
    return h;
  }

  _timedFetch(url, opts, ms = CONFIG.TIMEOUT) {
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), ms);
    return fetch(url, { ...opts, signal: ctrl.signal })
      .finally(() => clearTimeout(tid));
  }

  async login(username, password, remember = false) {
    try {
      const res  = await this._timedFetch(`${CONFIG.API_URL}/auth/login/`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify({ username, password }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || 'Login failed.');
      this.setSession(data.token, data.user, remember);
      return { success: true, user: data.user };
    } catch (e) {
      if (e.name === 'AbortError')
        return { success: false, error: 'Request timed out. Is the backend running on port 8000?' };
      if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError') || e.message.includes('fetch'))
        return { success: false, error: 'Cannot connect to backend. Make sure Django is running on http://localhost:8000' };
      return { success: false, error: e.message };
    }
  }

  async register(payload) {
    try {
      const res = await this._timedFetch(`${CONFIG.API_URL}/auth/register/`, {
        method : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body   : JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        const errMsg = data.error || extractApiError(data, 'Registration failed.');
        throw new Error(errMsg);
      }
      this.setSession(data.token, data.user, false);
      return { success: true, user: data.user };
    } catch (e) {
      if (e.name === 'AbortError')
        return { success: false, error: 'Request timed out. Is the backend running on port 8000?' };
      if (e.message.includes('Failed to fetch') || e.message.includes('NetworkError') || e.message.includes('fetch'))
        return { success: false, error: 'Cannot connect to backend. Make sure Django is running on http://localhost:8000' };
      return { success: false, error: e.message };
    }
  }

  async logout() {
    if (this.token) {
      fetch(`${CONFIG.API_URL}/auth/logout/`, {
        method   : 'POST',
        headers  : this.getHeaders(),
        keepalive: true,
      }).catch(() => {});
    }
    this.clear();
    window.location.href = loginPath();
  }

  async verify() {
    if (!this.token) return false;
    try {
      const res = await this._timedFetch(
        `${CONFIG.API_URL}/auth/verify/`,
        { headers: this.getHeaders() },
        5000
      );
      if (!res.ok) { this.clear(); return false; }
      const data = await res.json();
      if (data.authenticated) {
        this.updateStoredUser(data.user);
        return true;
      }
      this.clear();
      return false;
    } catch {
      // Network down — don't clear session, let user stay on page
      return false;
    }
  }
}

function extractApiError(data, fallback) {
  if (!data || typeof data !== 'object') return fallback;
  if (typeof data.message === 'string') return data.message;
  if (typeof data.detail === 'string') return data.detail;
  if (typeof data.error === 'string') return data.error;
  for (const [field, val] of Object.entries(data)) {
    if (Array.isArray(val) && val.length) {
      return field === 'non_field_errors' ? String(val[0]) : `${field}: ${val[0]}`;
    }
    if (typeof val === 'string') return `${field}: ${val}`;
  }
  return fallback;
}

/* ──────────────── CACHE MANAGER ──────────────── */
class CacheManager {
  constructor() { this._store = new Map(); }

  set(key, data, ttl = CONFIG.CACHE_TTL) {
    this._store.set(key, { data, expires: Date.now() + ttl });
  }

  get(key) {
    const item = this._store.get(key);
    if (!item) return null;
    if (Date.now() > item.expires) { this._store.delete(key); return null; }
    return item.data;
  }

  invalidate(prefix = '') {
    if (!prefix) { this._store.clear(); return; }
    for (const k of this._store.keys()) {
      if (k.startsWith(prefix)) this._store.delete(k);
    }
  }
}

/* ──────────────── API MANAGER ──────────────── */
class APIManager {
  constructor(auth, cache) {
    this.auth     = auth;
    this.cache    = cache;
    this._pending = new Map();
  }

  _timedFetch(url, opts, ms = CONFIG.TIMEOUT) {
    const ctrl = new AbortController();
    const tid  = setTimeout(() => ctrl.abort(), ms);
    return fetch(url, { ...opts, signal: ctrl.signal })
      .finally(() => clearTimeout(tid));
  }

  async _request(url, opts = {}, retries = CONFIG.MAX_RETRIES) {
    const full = `${CONFIG.API_URL}${url}`;
    const key  = `${opts.method || 'GET'}:${url}`;
    const deduplicate = (opts.method || 'GET') === 'GET';

    if (deduplicate && this._pending.has(key)) return this._pending.get(key);

    const promise = (async () => {
      try {
        const res = await this._timedFetch(full, {
          ...opts,
          headers: { ...this.auth.getHeaders(), ...(opts.headers || {}) },
        });

        if (res.status === 401) { await this.auth.logout(); throw new Error('Session expired.'); }
        if (res.status === 204) return {};

        const data = await res.json();
        if (!res.ok) {
          throw new Error(extractApiError(data, `HTTP ${res.status}`));
        }
        return data;

      } catch (e) {
        if (e.name === 'AbortError') throw new Error('Request timed out.');
        if (retries > 0 && (
          e.message.includes('fetch') ||
          e.message.includes('network') ||
          e.message.includes('Failed') ||
          e.message.includes('NetworkError')
        )) {
          await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY));
          if (this._pending.get(key) === promise) this._pending.delete(key);
          return this._request(url, opts, retries - 1);
        }
        throw e;
      } finally {
        if (this._pending.get(key) === promise) this._pending.delete(key);
      }
    })();

    if (deduplicate) this._pending.set(key, promise);
    return promise;
  }

  async getAll(url) {
    const separator = url.indexOf('?');
    const path = separator < 0 ? url : url.slice(0, separator);
    const params = new URLSearchParams(separator < 0 ? '' : url.slice(separator + 1));
    params.set('page_size', '200');

    const results = [];
    for (let page = 1; ; page++) {
      params.set('page', String(page));
      const data = await this.get(`${path}?${params.toString()}`, false);
      if (Array.isArray(data)) return data;
      if (!Array.isArray(data.results)) throw new Error('Invalid paginated response.');
      results.push(...data.results);
      if (!data.next || !data.results.length) return results;
    }
  }

  async get(url, useCache = true) {
    const cacheKey = `GET:${url}:${this.auth.user?.id}`;
    if (useCache) {
      const cached = this.cache.get(cacheKey);
      if (cached) return cached;
    }
    const data = await this._request(url);
    if (useCache) this.cache.set(cacheKey, data);
    return data;
  }

  post(url, body)  { this.cache.invalidate(); return this._request(url, { method: 'POST',   body: JSON.stringify(body) }); }
  put(url, body)   { this.cache.invalidate(); return this._request(url, { method: 'PUT',    body: JSON.stringify(body) }); }
  patch(url, body) { this.cache.invalidate(); return this._request(url, { method: 'PATCH',  body: JSON.stringify(body) }); }
  delete(url, body) {
    this.cache.invalidate();
    return this._request(url, {
      method: 'DELETE',
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  }
}

/* ──────────────── TOAST NOTIFICATIONS ──────────────── */
class Toast {
  static _queue   = [];
  static _visible = 0;
  static MAX      = 3;

  static show(msg, type = 'info', duration = 4500) {
    if (this._visible >= this.MAX) { this._queue.push({ msg, type, duration }); return; }
    this._render(msg, type, duration);
  }

  static _render(msg, type, duration) {
    this._visible++;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };

    let container = document.getElementById('ems-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'ems-toast-container';
      document.body.appendChild(container);
    }

    const el = document.createElement('div');
    el.className = `ems-toast ems-toast--${type}`;
    el.innerHTML = `<span class="ems-toast__icon">${icons[type] || icons.info}</span><span>${Utils.escapeHtml(String(msg))}</span>`;
    container.appendChild(el);
    requestAnimationFrame(() => el.classList.add('ems-toast--in'));

    const remove = () => {
      el.classList.remove('ems-toast--in');
      el.addEventListener('transitionend', () => {
        el.remove();
        this._visible--;
        if (this._queue.length) {
          const next = this._queue.shift();
          setTimeout(() => this._render(next.msg, next.type, next.duration), 80);
        }
      }, { once: true });
    };

    setTimeout(remove, duration);
    el.addEventListener('click', remove);
  }

  static success(m) { this.show(m, 'success'); }
  static error(m)   { this.show(m, 'error', 7000); }
  static warning(m) { this.show(m, 'warning', 5500); }
  static info(m)    { this.show(m, 'info'); }
}

/* ──────────────── UTILITIES ──────────────── */
const Utils = {
  safeIcon(icon, fallback = 'folder') {
    return typeof icon === 'string' && /^[a-z0-9-]+$/.test(icon) ? icon : fallback;
  },

  getCurrencyCode() {
    return auth?.user?.currency || 'NPR';
  },

  getCurrencySymbol() {
    if (auth?.user?.currency_symbol) return auth.user.currency_symbol;
    return CURRENCY_SYMBOLS[this.getCurrencyCode()] || 'Rs.';
  },

  formatCurrency(amount, symbol = null) {
    const n = parseFloat(amount) || 0;
    const sym = symbol || this.getCurrencySymbol();
    const code = this.getCurrencyCode();
    const locale = code === 'NPR' || code === 'INR' ? 'en-IN' : 'en-US';
    const hasDecimals = Math.abs(n % 1) >= 0.005;
    return `${sym}${n.toLocaleString(locale, {
      minimumFractionDigits: hasDecimals ? 2 : 0,
      maximumFractionDigits: 2,
    })}`;
  },

  formatCompactCurrency(amount, symbol = null) {
    const n = parseFloat(amount) || 0;
    const sym = symbol || this.getCurrencySymbol();
    if (Math.abs(n) >= 1_000_000) return `${sym}${(n / 1_000_000).toFixed(1)}M`;
    if (Math.abs(n) >= 1_000) return `${sym}${(n / 1_000).toFixed(0)}k`;
    return `${sym}${Math.round(n)}`;
  },

  formatDate(str, opts = { year: 'numeric', month: 'short', day: 'numeric' }) {
    if (!str) return '—';
    const d = new Date(str + (str.length === 10 ? 'T00:00:00' : ''));
    return isNaN(d) ? str : d.toLocaleDateString('en-US', opts);
  },

  relativeDate(str) {
    if (!str) return '—';
    const d    = new Date(str + 'T00:00:00');
    const days = Math.floor((Date.now() - d.getTime()) / 86400000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7)  return `${days}d ago`;
    return this.formatDate(str, { month: 'short', day: 'numeric' });
  },

  escapeHtml(s) {
    if (!s) return '';
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  },

  debounce(fn, ms = 350) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
  },

  downloadFile(content, name, type = 'text/plain') {
    const blob = new Blob([content], { type });
    const url  = URL.createObjectURL(blob);
    const a    = Object.assign(document.createElement('a'), { href: url, download: name });
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
  },
};

/* ──────────────── LOADER ──────────────── */
const Loader = {
  showBtn(btn, loading = true) {
    if (!btn) return;
    if (loading) {
      btn.disabled  = true;
      btn._orig     = btn.innerHTML;
      btn.innerHTML = `<span class="spinner-sm"></span> Loading…`;
    } else {
      btn.disabled  = false;
      btn.innerHTML = btn._orig || 'Submit';
    }
  },
};

/* ──────────────── CATEGORY LOADER ──────────────── */
const CategoryLoader = {
  _cache: null,

  async getAll() {
    if (!this._cache) {
      const data  = await api.get('/categories/');
      this._cache = Array.isArray(data) ? data : (data.results || []);
    }
    return this._cache;
  },

  async populateSelect(selectEl, placeholder = 'All Categories') {
    if (!selectEl) return;
    const categories = await this.getAll();
    const current    = selectEl.value;
    selectEl.innerHTML =
      `<option value="">${placeholder}</option>` +
      categories.map(c =>
        `<option value="${c.id}" ${c.id == current ? 'selected' : ''}>${Utils.escapeHtml(c.name)}</option>`
      ).join('');
  },

  invalidate() { this._cache = null; },
};

/* ──────────────── INIT ──────────────── */
const auth  = new AuthManager();
const cache = new CacheManager();
const api   = new APIManager(auth, cache);

window.AppCore = { auth, cache, api, Toast, Utils, Loader, CategoryLoader, ThemeManager, CONFIG };

/* ── requireAuth — call inside DOMContentLoaded on every protected page ── */
window.requireAuth = async () => {
  if (!auth.isAuthenticated()) {
    window.location.href = loginPath();
    return false;
  }
  const ok = await auth.verify();
  if (!ok) {
    window.location.href = loginPath();
    return false;
  }
  return true;
};

/* ──────────────── SIDEBAR ACTIVE STATE ──────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const page = window.location.pathname.split('/').pop();
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.getAttribute('href') === page);
  });

  const sidebar = document.querySelector('.sidebar');
  const topbarLeft = document.querySelector('.topbar__left');
  if (!sidebar || !topbarLeft) return;

  if (!sidebar.id) sidebar.id = 'emsSidebar';
  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'mobile-nav-toggle btn btn--ghost btn--icon btn--sm';
  toggle.setAttribute('aria-label', 'Open navigation');
  toggle.setAttribute('aria-controls', sidebar.id);
  toggle.setAttribute('aria-expanded', 'false');
  toggle.innerHTML = '<i class="fa-solid fa-bars" aria-hidden="true"></i>';
  topbarLeft.prepend(toggle);

  const backdrop = document.createElement('button');
  backdrop.type = 'button';
  backdrop.className = 'mobile-nav-backdrop';
  backdrop.setAttribute('aria-label', 'Close navigation');
  document.body.appendChild(backdrop);

  const setOpen = open => {
    sidebar.classList.toggle('open', open);
    backdrop.classList.toggle('open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    toggle.innerHTML = `<i class="fa-solid fa-${open ? 'xmark' : 'bars'}" aria-hidden="true"></i>`;
  };

  toggle.addEventListener('click', () => setOpen(!sidebar.classList.contains('open')));
  backdrop.addEventListener('click', () => setOpen(false));
  sidebar.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => setOpen(false));
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && sidebar.classList.contains('open')) setOpen(false);
  });
});

console.log('✅ EMS Core ready | API →', CONFIG.API_URL);