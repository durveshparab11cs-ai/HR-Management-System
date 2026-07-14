/**
 * settings.js — Settings and profile pages
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    SettingsPage.init();
});

const SettingsPage = {
    init() {
        this.initThemeToggle();
        this.initTimezonePreview();
    },

    initThemeToggle() {
        const toggle = document.getElementById('theme-toggle');
        if (!toggle) return;
        const html = document.documentElement;
        toggle.addEventListener('change', () => {
            html.dataset.bsTheme = toggle.checked ? 'dark' : 'light';
            HRMS.CSRF.post('/settings/theme', { theme: html.dataset.bsTheme }).catch(() => {});
        });
    },

    initTimezonePreview() {
        const select = document.getElementById('timezone-select');
        const preview = document.getElementById('timezone-preview');
        if (!select || !preview) return;
        const update = () => {
            try {
                const now = new Date().toLocaleString('en-US', { timeZone: select.value });
                preview.textContent = `Current time in this timezone: ${now}`;
            } catch (_) { preview.textContent = ''; }
        };
        select.addEventListener('change', update);
        update();
    },
};
