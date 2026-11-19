/* ═══════════════════════════════════════════════════
   EMS — Core Application Runtime (core.js)
   API Client, Auth, Theme, ConfirmModal, Toasts & Utils
═══════════════════════════════════════════════════ */
(() => {
  const isLocal = ['localhost', '127.0.0.1', ''].includes(window.location.hostname);
  const CONFIG = {
    API_URL: isLocal ? 'http://127.0.0.1:8000/api' : '/api',
    TOKEN_KEY: 'ems_auth_token',
    USER_KEY: 'ems_auth_user',
    THEME_KEY: 'ems_theme',
    CURRENCY_KEY: 'ems_currency',
  };

  const CURRENCIES = {
    NPR: { symbol: 'Rs.', decimals: 0 },
    USD: { symbol: '$', decimals: 2 },
    EUR: { symbol: '€', decimals: 2 },
    INR: { symbol: '₹', decimals: 0 },
    GBP: { symbol: '£', decimals: 2 },
  };

  /* ── THEME MANAGER ── */
  const ThemeManager = {
    init() {
      const saved = localStorage.getItem(CONFIG.THEME_KEY);
      if (saved === 'dark' || saved === 'light') {
        document.documentElement.setAttribute('data-theme', saved);
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
      this.syncIcons();
    },
    current() {
      const attr = document.documentElement.getAttribute('data-theme');
      if (attr) return attr;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    },
    set(theme) {
      if (theme === 'system') {
        localStorage.removeItem(CONFIG.THEME_KEY);
        document.documentElement.removeAttribute('data-theme');
      } else {
        localStorage.setItem(CONFIG.THEME_KEY, theme);
        document.documentElement.setAttribute('data-theme', theme);
      }
      this.syncIcons();
      window.dispatchEvent(new CustomEvent('ems:themechange', { detail: { theme: this.current() } }));
    },
    toggle() {
      this.set(this.current() === 'dark' ? 'light' : 'dark');
    },
    syncIcons() {
      const isDark = this.current() === 'dark';
      document.querySelectorAll('[data-theme-icon]').forEach(el => {
        el.className = isDark ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
      });
    },
  };

  /* ── CUSTOM CONFIRM MODAL ── */
  const ConfirmModal = {
    ask({ title = 'Confirm Action', message = 'Are you sure?', confirmText = 'Delete', danger = true } = {}) {
      return new Promise((resolve) => {
        let overlay = document.getElementById('ems-confirm-modal');
        if (!overlay) {
          overlay = document.createElement('div');
          overlay.id = 'ems-confirm-modal';
          overlay.className = 'modal-overlay';
          overlay.innerHTML = `
            <div class="modal" style="max-width:410px;">
              <div class="modal__header">
                <h3 class="modal__title" id="emsConfirmTitle"></h3>
                <button type="button" class="modal__close" id="emsConfirmClose" aria-label="Close">&times;</button>
              </div>
              <div class="modal__body">
                <p class="text-sm text-secondary" id="emsConfirmMsg" style="margin:0;line-height:1.6;"></p>
              </div>
              <div class="modal__footer">
                <button type="button" class="btn btn--ghost btn--sm" id="emsConfirmCancel">Cancel</button>
                <button type="button" class="btn btn--sm" id="emsConfirmOk"></button>
              </div>
            </div>`;
          document.body.appendChild(overlay);
        }

        const titleEl = overlay.querySelector('#emsConfirmTitle');
        const msgEl = overlay.querySelector('#emsConfirmMsg');
        const okBtn = overlay.querySelector('#emsConfirmOk');
        const cancelBtn = overlay.querySelector('#emsConfirmCancel');
        const closeBtn = overlay.querySelector('#emsConfirmClose');

        titleEl.textContent = title;
        msgEl.textContent = message;
        okBtn.innerHTML = danger
          ? `<i class="fa-solid fa-trash"></i><span>${Utils.escapeHtml(confirmText)}</span>`
          : `<span>${Utils.escapeHtml(confirmText)}</span>`;
        okBtn.className = `btn btn--sm ${danger ? 'btn--danger' : 'btn--primary'}`;

        const cleanup = (result) => {
          overlay.classList.remove('open');
          okBtn.onclick = null;
          cancelBtn.onclick = null;
          closeBtn.onclick = null;
          overlay.onclick = null;
          resolve(result);
        };

        okBtn.onclick = () => cleanup(true);
        cancelBtn.onclick = () => cleanup(false);
        closeBtn.onclick = () => cleanup(false);
        overlay.onclick = (e) => { if (e.target === overlay) cleanup(false); };

        overlay.classList.add('open');
        setTimeout(() => cancelBtn.focus(), 40);
      });
    },
  };

  /* ── TOAST NOTIFICATIONS ── */
  const Toast = {
    container() {
      let el = document.getElementById('ems-toast-container');
      if (!el) {
        el = document.createElement('div');
        el.id = 'ems-toast-container';
        document.body.appendChild(el);
      }
      return el;
    },
    show(msg, type = 'info', duration = 3400) {
      const icons = { success: '✓', error: '✕', warning: '!', info: 'i' };
      const t = document.createElement('div');
      t.className = `ems-toast ems-toast--${type}`;
      t.innerHTML = `<span class="ems-toast__icon">${icons[type] || 'i'}</span><span>${Utils.escapeHtml(msg)}</span>`;
      this.container().appendChild(t);
      requestAnimationFrame(() => t.classList.add('ems-toast--in'));
      const dismiss = () => {
        t.classList.remove('ems-toast--in');
        setTimeout(() => t.remove(), 260);
      };
      t.addEventListener('click', dismiss);
      setTimeout(dismiss, duration);
    },
    success(m) { this.show(m, 'success'); },
    error(m)   { this.show(m, 'error', 4500); },
    warning(m) { this.show(m, 'warning'); },
    info(m)    { this.show(m, 'info'); },
  };

  /* ── UTILITIES ── */
  const Utils = {
    escapeHtml(str) {
      return String(str ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    },
    getCurrency() {
      const user = auth.user;
      return localStorage.getItem(CONFIG.CURRENCY_KEY) || user?.currency || 'NPR';
    },
    formatCurrency(val, code) {
      const cur = CURRENCIES[code || this.getCurrency()] || CURRENCIES.NPR;
      const num = Number(val || 0);
      return `${cur.symbol}${num.toLocaleString('en-US', {
        minimumFractionDigits: cur.decimals,
        maximumFractionDigits: cur.decimals,
      })}`;
    },
    formatDate(iso) {
      if (!iso) return '—';
      const d = new Date(iso.includes('T') ? iso : `${iso}T00:00:00`);
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    },
    todayISO() {
      return new Date().toISOString().split('T')[0];
    },
    debounce(fn, wait = 260) {
      let timer;
      return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
      };
    },
    downloadFile(content, filename, mime = 'text/plain') {
      const blob = new Blob([content], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
  };

  /* ── BUTTON LOADER ── */
  const Loader = {
    showBtn(btn, loading) {
      if (!btn) return;
      if (loading) {
        btn.dataset.origHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<span class="spinner-sm"></span> <span>Working…</span>`;
      } else {
        btn.disabled = false;
        if (btn.dataset.origHtml) btn.innerHTML = btn.dataset.origHtml;
      }
    },
  };

  /* ── AUTH MANAGER ── */
  const auth = {
    get token() {
      return localStorage.getItem(CONFIG.TOKEN_KEY) || sessionStorage.getItem(CONFIG.TOKEN_KEY);
    },
    get user() {
      try {
        const raw = localStorage.getItem(CONFIG.USER_KEY) || sessionStorage.getItem(CONFIG.USER_KEY);
        return raw ? JSON.parse(raw) : null;
      } catch {
        return null;
      }
    },
    isAuthenticated() {
      return Boolean(this.token);
    },
    setSession(token, user, remember = true) {
      const store = remember ? localStorage : sessionStorage;
      const other = remember ? sessionStorage : localStorage;
      other.removeItem(CONFIG.TOKEN_KEY);
      other.removeItem(CONFIG.USER_KEY);
      store.setItem(CONFIG.TOKEN_KEY, token);
      if (user) {
        store.setItem(CONFIG.USER_KEY, JSON.stringify(user));
        if (user.currency) localStorage.setItem(CONFIG.CURRENCY_KEY, user.currency);
      }
    },
    clearSession() {
      [localStorage, sessionStorage].forEach(s => {
        s.removeItem(CONFIG.TOKEN_KEY);
        s.removeItem(CONFIG.USER_KEY);
      });
    },
    async login(username, password, remember = false) {
      try {
        const res = await fetch(`${CONFIG.API_URL}/auth/login/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
        const data = await res.json().catch(() => ({}));
        const token = data.token || data.data?.token || data.key || data.access;
        const user = data.user || data.data?.user;

        if (res.ok && token) {
          this.setSession(token, user, remember);
          return { success: true, user };
        }
        const errMsg =
          data.error ||
          data.detail ||
          data.message ||
          Object.values(data).flat().filter(Boolean)[0] ||
          `Invalid credentials (HTTP ${res.status}).`;
        return { success: false, error: typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg) };
      } catch {
        return { success: false, error: `Cannot connect to ${CONFIG.API_URL}. Check if the Django server is running.` };
      }
    },
    async verify() {
      if (!this.token) return false;
      try {
        await api.get('/categories/');
        if (this.user) hydrateUserShell(this.user);
        return true;
      } catch (err) {
        const msg = String(err?.message || '').toLowerCase();
        if (err?.status === 401 || err?.status === 403 || msg.includes('401') || msg.includes('403') || msg.includes('credential') || msg.includes('token')) {
          this.clearSession();
          return false;
        }
        if (this.user) hydrateUserShell(this.user);
        return true;
      }
    },
    async logout() {
      try {
        if (this.token) await api.post('/auth/logout/', {});
      } catch { /* ignore network failure during logout */ }
      this.clearSession();
      window.location.href = 'login.html';
    },
  };

  /* ── API CLIENT ── */
  const api = {
    async request(path, options = {}) {
      const headers = { ...(options.headers || {}) };
      if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
      }
      if (auth.token) {
        headers['Authorization'] = `Token ${auth.token}`;
      }
      const res = await fetch(`${CONFIG.API_URL}${path}`, { ...options, headers });
      if (res.status === 204) return null;
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const errMsg =
          data.error ||
          data.detail ||
          Object.values(data).flat().filter(Boolean)[0] ||
          `Request failed (${res.status})`;
        const error = new Error(typeof errMsg === 'string' ? errMsg : JSON.stringify(errMsg));
        error.status = res.status;
        throw error;
      }
      return data;
    },
    get(path)         { return this.request(path, { method: 'GET' }); },
    post(path, body)  { return this.request(path, { method: 'POST', body: JSON.stringify(body) }); },
    put(path, body)   { return this.request(path, { method: 'PUT', body: JSON.stringify(body) }); },
    patch(path, body) { return this.request(path, { method: 'PATCH', body: JSON.stringify(body) }); },
    delete(path)      { return this.request(path, { method: 'DELETE' }); },
    async getAll(path) {
      const data = await this.get(path);
      if (Array.isArray(data)) return data;
      if (data && Array.isArray(data.results)) {
        let items = [...data.results];
        let nextUrl = data.next;
        while (nextUrl) {
          const nextPath = nextUrl.replace(CONFIG.API_URL, '');
          const page = await this.get(nextPath);
          items = items.concat(page.results || []);
          nextUrl = page.next;
        }
        return items;
      }
      return [];
    },
  };

  /* ── CATEGORY LOADER ── */
  const CategoryLoader = {
    cache: null,
    async load(force = false) {
      if (this.cache && !force) return this.cache;
      this.cache = await api.getAll('/categories/');
      return this.cache;
    },
    async populateSelect(selectEl, placeholder = 'Select Category') {
      if (!selectEl) return [];
      const cats = await this.load();
      selectEl.innerHTML = `<option value="">${Utils.escapeHtml(placeholder)}</option>` +
        cats.map(c => `<option value="${c.id}">${Utils.escapeHtml(c.name)}</option>`).join('');
      return cats;
    },
  };

  /* ── USER SHELL HYDRATION ── */
  function hydrateUserShell(user) {
    if (!user) return;
    const displayName = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.username || 'User';
    const initial = (user.first_name?.[0] || user.username?.[0] || 'U').toUpperCase();

    ['sidebarName', 'sidebarUserName'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = displayName;
    });
    const avatarEl = document.getElementById('sidebarAvatar');
    if (avatarEl) avatarEl.textContent = initial;
    const emailEl = document.getElementById('sidebarUserEmail');
    if (emailEl) emailEl.textContent = user.email || 'Personal Account';
  }

  window.requireAuth = async () => {
    if (!auth.isAuthenticated()) {
      window.location.href = 'login.html';
      return false;
    }
    const valid = await auth.verify();
    if (!valid) {
      window.location.href = 'login.html';
      return false;
    }
    return true;
  };

  ThemeManager.init();

  window.AppCore = {
    CONFIG,
    CURRENCIES,
    ThemeManager,
    ConfirmModal,
    Toast,
    Utils,
    Loader,
    auth,
    api,
    CategoryLoader,
    hydrateUserShell,
  };
})();