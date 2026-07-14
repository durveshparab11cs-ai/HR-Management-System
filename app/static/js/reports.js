/**
 * reports.js — Report filter forms and export triggers
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    ReportsPage.init();
});

const ReportsPage = {
    init() {
        this.initExportButtons();
        this.initDateDefaults();
    },

    initExportButtons() {
        document.querySelectorAll('[data-export-format]').forEach(btn => {
            btn.addEventListener('click', () => {
                const form = document.getElementById('report-filter-form');
                if (form) {
                    const hidden = document.createElement('input');
                    hidden.type  = 'hidden';
                    hidden.name  = 'format';
                    hidden.value = btn.dataset.exportFormat;
                    form.appendChild(hidden);
                    form.submit();
                    form.removeChild(hidden);
                }
            });
        });
    },

    initDateDefaults() {
        const startEl = document.getElementById('report-start-date');
        const endEl   = document.getElementById('report-end-date');
        if (!startEl || !endEl) return;
        const today = new Date().toISOString().split('T')[0];
        const firstOfMonth = today.slice(0, 8) + '01';
        if (!startEl.value) startEl.value = firstOfMonth;
        if (!endEl.value)   endEl.value   = today;
    },
};
