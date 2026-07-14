/**
 * auth.js
 * ========
 * JavaScript for authentication pages: login, register, password reset.
 *
 * Responsibilities:
 *   - Real-time password strength meter
 *   - Confirm-password match validation
 *   - Login form submission with loading state
 *
 * Depends on: common.js (HRMS namespace must be loaded first)
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    AuthPage.initPasswordStrength();
    AuthPage.initPasswordMatch();
    AuthPage.initLoginForm();
});

const AuthPage = {

    /* ── Password strength meter ──────────────────────────────────── */

    initPasswordStrength() {
        const input = document.getElementById('password');
        const bar   = document.getElementById('password-strength-bar');
        if (!input || !bar) return;

        bar.innerHTML = '<div class="hrms-password-strength-fill"></div>';

        input.addEventListener('input', () => {
            const { score, label } = this._scorePassword(input.value);
            const fill = bar.querySelector('.hrms-password-strength-fill');
            const pct  = ['0%', '25%', '50%', '75%', '100%'][score];
            const cls  = ['', 'strength-weak', 'strength-fair', 'strength-good', 'strength-strong'][score];

            fill.style.width = pct;
            bar.className    = `hrms-password-strength ${cls}`;
            fill.title       = label;
        });
    },

    /**
     * Score a password from 0 (empty) to 4 (strong).
     * @param {string} pwd
     * @returns {{ score: number, label: string }}
     */
    _scorePassword(pwd) {
        if (!pwd) return { score: 0, label: '' };
        let score = 0;
        if (pwd.length >= 8)  score++;
        if (pwd.length >= 12) score++;
        if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score++;
        if (/\d/.test(pwd) && /[^A-Za-z0-9]/.test(pwd)) score++;
        const labels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
        return { score, label: labels[score] };
    },

    /* ── Confirm password match ───────────────────────────────────── */

    initPasswordMatch() {
        const pwd     = document.getElementById('password');
        const confirm = document.getElementById('confirm_password');
        if (!pwd || !confirm) return;

        const validate = () => {
            if (confirm.value && confirm.value !== pwd.value) {
                confirm.setCustomValidity('Passwords do not match.');
                confirm.classList.add('is-invalid');
            } else {
                confirm.setCustomValidity('');
                confirm.classList.remove('is-invalid');
            }
        };

        pwd.addEventListener('input', validate);
        confirm.addEventListener('input', validate);
    },

    /* ── Login form ───────────────────────────────────────────────── */

    initLoginForm() {
        const form = document.getElementById('login-form');
        if (!form) return;

        form.addEventListener('submit', () => {
            const btn     = document.getElementById('login-submit-btn');
            const text    = btn?.querySelector('.hrms-btn-text');
            const spinner = btn?.querySelector('.hrms-btn-spinner');
            if (btn) {
                btn.disabled = true;
                text?.classList.add('d-none');
                spinner?.classList.remove('d-none');
            }
        });
    },
};
