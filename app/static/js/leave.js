/**
 * leave.js — Leave application form and calendar page
 */
'use strict';

document.addEventListener('DOMContentLoaded', () => {
    LeaveApp.init();
});

const LeaveApp = {
    init() {
        this.initDateRange();
        this.initDayCount();
    },

    initDateRange() {
        const start = document.getElementById('leave-start');
        const end   = document.getElementById('leave-end');
        if (!start || !end) return;

        start.addEventListener('change', () => {
            end.min = start.value;
            if (end.value && end.value < start.value) end.value = start.value;
            this.updateDayCount(start.value, end.value);
        });

        end.addEventListener('change', () => {
            this.updateDayCount(start.value, end.value);
        });
    },

    initDayCount() {
        const start = document.getElementById('leave-start')?.value;
        const end   = document.getElementById('leave-end')?.value;
        if (start && end) this.updateDayCount(start, end);
    },

    updateDayCount(start, end) {
        const el = document.getElementById('leave-day-count');
        if (!el || !start || !end) return;
        const ms   = new Date(end) - new Date(start);
        const days = Math.max(0, Math.floor(ms / 86400000) + 1);
        el.textContent = `${days} day${days !== 1 ? 's' : ''}`;
    },
};
