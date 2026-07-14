/**
 * employees.js
 * =============
 * Employee directory and profile pages:
 *   - Live search filtering
 *   - Profile photo preview on file select
 *   - Delete confirmation modal
 *   - Tab persistence via URL hash
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    EmployeesPage.init();
});

const EmployeesPage = {

    init() {
        this.initSearch();
        this.initPhotoPreview();
        this.initDeleteConfirm();
        this.initTabPersistence();
    },

    /* ── Live search ──────────────────────────────────────────────── */

    initSearch() {
        const input = document.getElementById('employee-search');
        const rows  = document.querySelectorAll('[data-employee-row]');
        if (!input || !rows.length) return;

        const filter = HRMS.Utils.debounce(() => {
            const query = input.value.toLowerCase().trim();
            rows.forEach(row => {
                const text  = row.textContent.toLowerCase();
                const match = !query || text.includes(query);
                row.style.display = match ? '' : 'none';
            });
        }, 250);

        input.addEventListener('input', filter);
    },

    /* ── Profile photo preview ────────────────────────────────────── */

    initPhotoPreview() {
        const input   = document.getElementById('profile-photo-input');
        const preview = document.getElementById('profile-photo-preview');
        if (!input || !preview) return;

        input.addEventListener('change', () => {
            const file = input.files[0];
            if (!file) return;

            const maxMB = 5;
            if (file.size > maxMB * 1024 * 1024) {
                HRMS.Flash.show(`File exceeds the ${maxMB}MB limit.`, 'danger');
                input.value = '';
                return;
            }

            const allowed = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'];
            if (!allowed.includes(file.type)) {
                HRMS.Flash.show('Please upload a PNG, JPG, WEBP, or GIF image.', 'danger');
                input.value = '';
                return;
            }

            const reader = new FileReader();
            reader.onload = e => { preview.src = e.target.result; };
            reader.readAsDataURL(file);
        });
    },

    /* ── Delete confirmation ──────────────────────────────────────── */

    initDeleteConfirm() {
        document.querySelectorAll('[data-confirm-delete]').forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                const name = btn.dataset.employeeName || 'this employee';
                const href = btn.getAttribute('href') || btn.dataset.action;

                HRMS.Modal.confirm({
                    title: 'Delete Employee',
                    body:  `<p class="mb-0">Are you sure you want to delete <strong>${HRMS.Utils.escapeHtml(name)}</strong>? This action cannot be undone.</p>`,
                    confirmLabel: 'Delete',
                    confirmClass: 'btn-danger',
                    onConfirm: () => { if (href) window.location.href = href; },
                });
            });
        });
    },

    /* ── Tab persistence ──────────────────────────────────────────── */

    initTabPersistence() {
        const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
        if (!tabs.length) return;

        // Restore active tab from URL hash
        const hash = window.location.hash;
        if (hash) {
            const tab = document.querySelector(`[data-bs-target="${hash}"]`);
            if (tab) bootstrap.Tab.getOrCreateInstance(tab).show();
        }

        // Update hash on tab change
        tabs.forEach(tab => {
            tab.addEventListener('shown.bs.tab', e => {
                const target = e.target.dataset.bsTarget || e.target.getAttribute('href');
                if (target) history.replaceState(null, '', target);
            });
        });
    },
};
