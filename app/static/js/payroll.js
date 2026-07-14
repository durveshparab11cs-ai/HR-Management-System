/**
 * payroll.js — Payroll processing and payslip pages
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    PayrollPage.init();
});

const PayrollPage = {
    init() {
        this.initPrintPayslip();
        this.initSalaryCalculator();
    },

    initPrintPayslip() {
        const btn = document.getElementById('print-payslip-btn');
        btn?.addEventListener('click', () => window.print());
    },

    initSalaryCalculator() {
        const fields    = document.querySelectorAll('[data-salary-component]');
        const totalEl   = document.getElementById('gross-salary-display');
        if (!fields.length || !totalEl) return;

        const recalc = () => {
            let total = 0;
            fields.forEach(f => { total += parseFloat(f.value) || 0; });
            totalEl.textContent = HRMS.Utils.formatCurrency(total);
        };

        fields.forEach(f => f.addEventListener('input', recalc));
        recalc();
    },
};
