/**
 * common.js
 * ==========
 * Global JavaScript loaded on every authenticated page.
 *
 * Responsibilities:
 *   - Sidebar toggle (mobile)
 *   - Flash message auto-dismiss
 *   - CSRF token injection for AJAX requests
 *   - Global confirmation modal (HRMSModal)
 *   - Password visibility toggle
 *   - Form submit loading state
 *   - Notification badge polling
 *   - Global AJAX error handler
 *   - Tooltip / popover initialization
 *
 * No framework dependencies — Vanilla ES6 + Bootstrap 5.
 * All functions are namespaced under the `HRMS` global object.
 */

'use strict';

/* ─── Namespace ─────────────────────────────────────────────────────── */

window.HRMS = window.HRMS || {};

/* ─── DOM Ready ─────────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
    HRMS.Sidebar.init();
    HRMS.Flash.init();
    HRMS.Forms.init();
    HRMS.PasswordToggle.init();
    HRMS.Tooltips.init();
    HRMS.Notifications.init();
    HRMS.CSRF.init();
    HRMS.Dashboard.initDate();
});

/* ─── CSRF ──────────────────────────────────────────────────────────── */

HRMS.CSRF = {
    token: null,

    init() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        this.token = meta ? meta.content : null;
    },

    /**
     * Returns headers object with CSRF token for fetch() calls.
     * @returns {Object}
     */
    headers() {
        return this.token
            ? { 'X-CSRFToken': this.token, 'X-Requested-With': 'XMLHttpRequest' }
            : { 'X-Requested-With': 'XMLHttpRequest' };
    },

    /**
     * Convenience: POST JSON with CSRF token.
     * @param {string} url
     * @param {Object} data
     * @returns {Promise<Response>}
     */
    async post(url, data = {}) {
        return fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...this.headers() },
            body: JSON.stringify(data),
        });
    },
};

/* ─── Sidebar ───────────────────────────────────────────────────────── */

HRMS.Sidebar = {
    sidebar: null,
    overlay: null,
    toggleBtn: null,
    closeBtn: null,

    init() {
        this.sidebar   = document.getElementById('hrms-sidebar');
        this.overlay   = document.getElementById('sidebar-overlay');
        this.toggleBtn = document.getElementById('sidebar-toggle-btn');
        this.closeBtn  = document.getElementById('sidebar-close-btn');

        if (!this.sidebar) return;

        this.toggleBtn?.addEventListener('click', () => this.open());
        this.closeBtn?.addEventListener('click',  () => this.close());
        this.overlay?.addEventListener('click',   () => this.close());

        // Close on Escape
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') this.close();
        });
    },

    open() {
        this.sidebar.classList.add('show');
        this.overlay?.classList.add('show');
        this.toggleBtn?.setAttribute('aria-expanded', 'true');
        document.body.style.overflow = 'hidden';
    },

    close() {
        this.sidebar.classList.remove('show');
        this.overlay?.classList.remove('show');
        this.toggleBtn?.setAttribute('aria-expanded', 'false');
        document.body.style.overflow = '';
    },
};

/* ─── Flash Messages ────────────────────────────────────────────────── */

HRMS.Flash = {
    AUTO_DISMISS_MS: 5000,

    init() {
        document.querySelectorAll('.hrms-flash-alert[data-auto-dismiss="true"]')
            .forEach(el => this._scheduleClose(el));
    },

    _scheduleClose(el) {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            bsAlert.close();
        }, this.AUTO_DISMISS_MS);
    },

    /**
     * Programmatically show a flash message.
     * @param {string} message
     * @param {'success'|'danger'|'warning'|'info'} category
     */
    show(message, category = 'info') {
        const icons = {
            success: 'bi-check-circle-fill',
            danger:  'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info:    'bi-info-circle-fill',
        };
        const icon  = icons[category] || icons.info;
        const alert = document.createElement('div');
        alert.className = `alert alert-${category} alert-dismissible fade show d-flex align-items-start gap-2 hrms-flash-alert`;
        alert.setAttribute('role', 'alert');
        alert.innerHTML = `
            <i class="bi ${icon} flex-shrink-0 mt-1" aria-hidden="true"></i>
            <div class="flex-grow-1">${HRMS.Utils.escapeHtml(message)}</div>
            <button type="button" class="btn-close ms-2" data-bs-dismiss="alert" aria-label="Close"></button>`;

        let container = document.querySelector('.hrms-flash-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'hrms-flash-container';
            document.querySelector('.hrms-content')?.prepend(container);
        }
        container.appendChild(alert);

        if (category === 'success' || category === 'info') {
            this._scheduleClose(alert);
        }
    },
};

/* ─── Forms ─────────────────────────────────────────────────────────── */

HRMS.Forms = {
    init() {
        // Bootstrap validation on submit
        document.querySelectorAll('form[novalidate]').forEach(form => {
            form.addEventListener('submit', e => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });

        // Loading state on form submit buttons
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', () => {
                const btn    = form.querySelector('[type="submit"]');
                const text   = btn?.querySelector('.hrms-btn-text');
                const spinner = btn?.querySelector('.hrms-btn-spinner');
                if (btn && form.checkValidity()) {
                    btn.disabled = true;
                    text?.classList.add('d-none');
                    spinner?.classList.remove('d-none');
                }
            });
        });
    },
};

/* ─── Password Visibility Toggle ────────────────────────────────────── */

HRMS.PasswordToggle = {
    init() {
        document.querySelectorAll('.hrms-password-toggle').forEach(btn => {
            btn.addEventListener('click', () => {
                const input = btn.closest('.input-group')?.querySelector('input[type="password"], input[type="text"]');
                if (!input) return;
                const isPassword = input.type === 'password';
                input.type       = isPassword ? 'text' : 'password';
                const icon       = btn.querySelector('.bi');
                icon?.classList.toggle('bi-eye', !isPassword);
                icon?.classList.toggle('bi-eye-slash', isPassword);
                btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
            });
        });
    },
};

/* ─── Tooltips & Popovers ───────────────────────────────────────────── */

HRMS.Tooltips = {
    init() {
        document.querySelectorAll('[data-bs-toggle="tooltip"]')
            .forEach(el => new bootstrap.Tooltip(el, { trigger: 'hover focus' }));
        document.querySelectorAll('[data-bs-toggle="popover"]')
            .forEach(el => new bootstrap.Popover(el));
    },
};

/* ─── Confirmation Modal ────────────────────────────────────────────── */

HRMS.Modal = {
    _instance: null,

    /**
     * Show the global confirmation modal.
     * @param {Object} opts
     * @param {string} opts.title
     * @param {string} opts.body
     * @param {string} [opts.confirmLabel]
     * @param {string} [opts.confirmClass]
     * @param {Function} opts.onConfirm
     */
    confirm({ title, body, confirmLabel = 'Confirm', confirmClass = 'btn-danger', onConfirm }) {
        const el = document.getElementById('hrms-global-modal');
        if (!el) return;

        el.querySelector('#hrms-modal-title').textContent = title;
        el.querySelector('#hrms-modal-body').innerHTML    = body;

        const confirmBtn  = el.querySelector('#hrms-modal-confirm-btn');
        confirmBtn.textContent = confirmLabel;
        confirmBtn.className   = `btn ${confirmClass} hrms-modal-confirm-btn`;

        // Remove previous listener clone trick
        const newBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);
        newBtn.addEventListener('click', () => {
            this._instance?.hide();
            onConfirm?.();
        });

        this._instance = bootstrap.Modal.getOrCreateInstance(el);
        this._instance.show();
    },
};

/* ─── Notifications ─────────────────────────────────────────────────── */

HRMS.Notifications = {
    POLL_INTERVAL_MS: 60_000,
    _timer: null,

    init() {
        const badge = document.getElementById('notification-count');
        if (!badge) return;

        this._poll();
        this._timer = setInterval(() => this._poll(), this.POLL_INTERVAL_MS);
    },

    async _poll() {
        try {
            const res  = await fetch('/notifications/count', { headers: HRMS.CSRF.headers() });
            if (!res.ok) return;
            const data = await res.json();
            const count = data.unread || 0;
            const badge = document.getElementById('notification-count');
            if (!badge) return;
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = '';
            } else {
                badge.style.display = 'none';
            }
        } catch (_) { /* silently ignore network errors */ }
    },
};

/* ─── Dashboard date display ────────────────────────────────────────── */

HRMS.Dashboard = {
    initDate() {
        const el = document.getElementById('dashboard-date');
        if (!el) return;
        const now = new Date();
        el.textContent = now.toLocaleDateString(undefined, {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
        });
    },
};

/* ─── Utilities ─────────────────────────────────────────────────────── */

HRMS.Utils = {
    /**
     * Escape HTML special characters to prevent XSS in dynamic innerHTML.
     * @param {string} str
     * @returns {string}
     */
    escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    },

    /**
     * Debounce a function call.
     * @param {Function} fn
     * @param {number} wait
     * @returns {Function}
     */
    debounce(fn, wait = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), wait);
        };
    },

    /**
     * Format a number as currency string.
     * @param {number} value
     * @param {string} [symbol]
     * @returns {string}
     */
    formatCurrency(value, symbol = '₹') {
        return symbol + Number(value).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    },

    /**
     * Format bytes to human-readable size.
     * @param {number} bytes
     * @returns {string}
     */
    formatFileSize(bytes) {
        if (bytes < 1024)       return bytes + ' B';
        if (bytes < 1048576)    return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    },
};
