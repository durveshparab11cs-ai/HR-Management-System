/**
 * admin.js — Admin panel: user management, audit log viewer
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    AdminPage.init();
});

const AdminPage = {
    init() {
        this.initUserActions();
        this.initAuditFilter();
    },

    initUserActions() {
        document.querySelectorAll('[data-action="suspend-user"]').forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                const name = btn.dataset.userName || 'this user';
                HRMS.Modal.confirm({
                    title: 'Suspend User Account',
                    body:  `<p class="mb-0">Suspend <strong>${HRMS.Utils.escapeHtml(name)}</strong>? They will be unable to log in.</p>`,
                    confirmLabel: 'Suspend',
                    confirmClass: 'btn-warning',
                    onConfirm: () => { window.location.href = btn.dataset.url; },
                });
            });
        });
    },

    initAuditFilter() {
        const input = document.getElementById('audit-search');
        const rows  = document.querySelectorAll('[data-audit-row]');
        if (!input || !rows.length) return;

        const filter = HRMS.Utils.debounce(() => {
            const q = input.value.toLowerCase();
            rows.forEach(r => {
                r.style.display = !q || r.textContent.toLowerCase().includes(q) ? '' : 'none';
            });
        }, 250);

        input.addEventListener('input', filter);
    },
};
