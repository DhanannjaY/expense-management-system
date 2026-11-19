/* ═══════════════════════════════════════════════════
   EMS — Global UI Shell & Interaction Controller (main.js)
   Mobile Drawer, Pill Theme Switcher, Budget Badge,
   Keyboard Shortcuts & Chart.js Theme Tokens
═══════════════════════════════════════════════════ */
(() => {
  const AppMain = {
    init() {
      if (!window.AppCore) return;
      const { auth, hydrateUserShell } = window.AppCore;

      this.setupMobileDrawer();
      this.setupTopbarThemeToggle();
      this.setupKeyboardShortcuts();
      this.highlightActiveNav();

      if (auth.user) hydrateUserShell(auth.user);
      if (auth.isAuthenticated() && document.querySelector('.sidebar')) {
        this.syncBudgetAlertBadge();
      }
    },

    /* ── 1. MOBILE NAVIGATION DRAWER ── */
    setupMobileDrawer() {
      const sidebar = document.querySelector('.sidebar');
      const topbarLeft = document.querySelector('.topbar__left');
      if (!sidebar || !topbarLeft || document.querySelector('.mobile-nav-toggle')) return;

      const toggleBtn = document.createElement('button');
      toggleBtn.type = 'button';
      toggleBtn.className = 'btn btn--ghost btn--icon btn--sm mobile-nav-toggle';
      toggleBtn.setAttribute('aria-label', 'Open navigation menu');
      toggleBtn.innerHTML = '<i class="fa-solid fa-bars"></i>';
      topbarLeft.prepend(toggleBtn);

      const backdrop = document.createElement('button');
      backdrop.type = 'button';
      backdrop.className = 'mobile-nav-backdrop';
      backdrop.setAttribute('aria-label', 'Close navigation menu');
      document.body.appendChild(backdrop);

      const closeDrawer = () => {
        sidebar.classList.remove('open');
        backdrop.classList.remove('open');
        document.body.style.overflow = '';
      };

      const openDrawer = () => {
        sidebar.classList.add('open');
        backdrop.classList.add('open');
        document.body.style.overflow = 'hidden';
      };

      toggleBtn.addEventListener('click', () => {
        sidebar.classList.contains('open') ? closeDrawer() : openDrawer();
      });
      backdrop.addEventListener('click', closeDrawer);
      sidebar.querySelectorAll('.nav-link').forEach(link => link.addEventListener('click', closeDrawer));

      window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && sidebar.classList.contains('open')) {
          closeDrawer();
        }
      });
    },

    /* ── 2. SEGMENTED PILL LIGHT / DARK THEME TOGGLE ── */
    setupTopbarThemeToggle() {
      const topbarRight = document.querySelector('.topbar__right');
      if (!topbarRight || document.getElementById('globalThemeBtn')) return;

      const { ThemeManager } = window.AppCore;
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.id = 'globalThemeBtn';
      pill.className = 'theme-pill-toggle';
      pill.title = 'Switch Light / Dark theme';
      pill.setAttribute('aria-label', 'Switch Light or Dark theme');
      pill.innerHTML = `
        <span class="theme-pill-toggle__opt" data-mode="light"><i class="fa-solid fa-sun"></i></span>
        <span class="theme-pill-toggle__opt" data-mode="dark"><i class="fa-solid fa-moon"></i></span>
      `;

      const syncPill = () => {
        const cur = ThemeManager.current();
        pill.querySelectorAll('.theme-pill-toggle__opt').forEach(opt => {
          opt.classList.toggle('active', opt.dataset.mode === cur);
        });
      };

      pill.addEventListener('click', () => {
        ThemeManager.toggle();
        syncPill();
      });
      window.addEventListener('ems:themechange', syncPill);

      topbarRight.prepend(pill);
      syncPill();
    },

    /* ── 3. AUTOMATIC ACTIVE SIDEBAR LINK ── */
    highlightActiveNav() {
      const currentFile = window.location.pathname.split('/').pop() || 'dashboard.html';
      document.querySelectorAll('.sidebar__nav .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentFile) {
          link.classList.add('active');
        }
      });
    },

    /* ── 4. LIVE SIDEBAR BUDGET WARNING BADGE ── */
    async syncBudgetAlertBadge() {
      const { api } = window.AppCore;
      try {
        const budgets = await api.getAll('/budgets/');
        const warnCount = budgets.filter(b => {
          const limit = parseFloat(b.amount || 0);
          const spent = parseFloat(b.spent || 0);
          if (limit <= 0) return false;
          return (spent / limit) * 100 >= (b.alert_threshold || 80);
        }).length;

        const budgetLink = document.querySelector('.sidebar__nav a[href="budget.html"]');
        if (!budgetLink) return;

        let badge = document.getElementById('navBudgetAlert');
        if (!badge && warnCount > 0) {
          badge = document.createElement('span');
          badge.id = 'navBudgetAlert';
          badge.className = 'badge';
          budgetLink.appendChild(badge);
        }
        if (badge) {
          if (warnCount > 0) {
            badge.textContent = String(warnCount);
            badge.classList.remove('hidden');
          } else {
            badge.classList.add('hidden');
          }
        }
      } catch { /* silent background check */ }
    },

    /* ── 5. GLOBAL KEYBOARD SHORTCUTS ── */
    setupKeyboardShortcuts() {
      document.addEventListener('keydown', e => {
        if (e.key === 'Escape') {
          document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
          const sidebar = document.querySelector('.sidebar.open');
          const backdrop = document.querySelector('.mobile-nav-backdrop.open');
          if (sidebar) sidebar.classList.remove('open');
          if (backdrop) backdrop.classList.remove('open');
          document.body.style.overflow = '';
          return;
        }

        const tag = document.activeElement?.tagName;
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tag) || document.activeElement?.isContentEditable) {
          return;
        }

        if (e.key.toLowerCase() === 'n' && !e.ctrlKey && !e.metaKey && !e.altKey) {
          const primaryAdd = document.querySelector('#addExpenseTopBtn, #newBudgetBtn, #newGoalBtn');
          if (primaryAdd) {
            e.preventDefault();
            primaryAdd.click();
          }
        }
      });
    },

    /* ── 6. SHARED CHART.JS THEME HELPER ── */
    getChartTheme() {
      const isDark = window.AppCore?.ThemeManager.current() === 'dark';
      return {
        isDark,
        gridColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
        tickColor: isDark ? '#a8a8c0' : '#7c7c98',
        tooltipBg: isDark ? '#1c1c28' : '#14141e',
        palette: ['#7c3aed', '#10b981', '#0ea5e9', '#f59e0b', '#f43f5e', '#6366f1', '#14b8a6'],
      };
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AppMain.init());
  } else {
    AppMain.init();
  }

  window.AppMain = AppMain;
})();