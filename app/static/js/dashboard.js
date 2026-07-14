/**
 * dashboard.js
 * =============
 * Dashboard page scripts.
 * Charts are driven by real data injected from the server via
 * <script id="dashboard-data"> JSON blocks in the template.
 * No random/fake data is used anywhere.
 */

'use strict';

document.addEventListener('DOMContentLoaded', () => {
    DashboardPage.init();
});

const DashboardPage = {

    init() {
        this.initClock();
        this.initAttendanceChart();
        this.initDepartmentChart();
    },

    /* ── Live clock ───────────────────────────────────────────────── */

    initClock() {
        const el = document.getElementById('dashboard-date');
        if (!el) return;
        const update = () => {
            el.textContent = new Date().toLocaleDateString(undefined, {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
            });
        };
        update();
        const msToMidnight = () => {
            const n = new Date();
            return (86400 - n.getHours() * 3600 - n.getMinutes() * 60 - n.getSeconds()) * 1000;
        };
        setTimeout(() => { update(); setInterval(update, 86400000); }, msToMidnight());
    },

    /* ── Attendance bar chart — data from server ──────────────────── */

    initAttendanceChart() {
        const canvas = document.getElementById('attendance-chart');
        if (!canvas || typeof Chart === 'undefined') return;

        // Data is embedded by the server in a JSON script tag.
        // If no data is available, show a "no data" message.
        const raw = document.getElementById('attendance-chart-data');
        if (!raw) {
            this._showNoData(canvas, 'No attendance data available yet.');
            return;
        }

        let chartData;
        try {
            chartData = JSON.parse(raw.textContent);
        } catch (_) {
            this._showNoData(canvas, 'Could not load attendance data.');
            return;
        }

        new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: chartData.labels,
                datasets: [
                    {
                        label: 'Present',
                        data: chartData.present,
                        backgroundColor: 'rgba(25, 135, 84, 0.75)',
                        borderRadius: 4,
                    },
                    {
                        label: 'Absent',
                        data: chartData.absent,
                        backgroundColor: 'rgba(220, 53, 69, 0.65)',
                        borderRadius: 4,
                    },
                    {
                        label: 'On Leave',
                        data: chartData.on_leave,
                        backgroundColor: 'rgba(255, 193, 7, 0.65)',
                        borderRadius: 4,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { usePointStyle: true, boxWidth: 8 } },
                    tooltip: { mode: 'index', intersect: false },
                },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.05)' }, ticks: { precision: 0 } },
                },
            },
        });
    },

    /* ── Department doughnut chart — data from server ─────────────── */

    initDepartmentChart() {
        const canvas = document.getElementById('department-chart');
        if (!canvas || typeof Chart === 'undefined') return;

        const raw = document.getElementById('department-chart-data');
        if (!raw) {
            this._showNoData(canvas, 'No department data available yet.');
            return;
        }

        let chartData;
        try {
            chartData = JSON.parse(raw.textContent);
        } catch (_) {
            this._showNoData(canvas, 'Could not load department data.');
            return;
        }

        if (!chartData.labels || chartData.labels.length === 0) {
            this._showNoData(canvas, 'No departments configured yet.');
            return;
        }

        new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: chartData.labels,
                datasets: [{
                    data: chartData.values,
                    backgroundColor: [
                        '#1a3c6e', '#2a5298', '#f59e0b', '#198754',
                        '#6c757d', '#0dcaf0', '#d63384', '#fd7e14',
                    ],
                    borderWidth: 0,
                    hoverOffset: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '68%',
                plugins: {
                    legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 14 } },
                },
            },
        });
    },

    /* ── Helpers ──────────────────────────────────────────────────── */

    _showNoData(canvas, message) {
        const wrapper = canvas.parentElement;
        canvas.style.display = 'none';
        const msg = document.createElement('div');
        msg.className = 'text-center text-muted py-5 small';
        msg.innerHTML = `<i class="bi bi-bar-chart" style="font-size:2rem;opacity:.3;display:block;margin-bottom:8px"></i>${message}`;
        wrapper.appendChild(msg);
    },
};
