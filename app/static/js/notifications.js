/**
 * Notification Bell and Real-time Updates
 * ========================================
 * Handles notification dropdown, real-time updates, and user interactions
 */

(function() {
    'use strict';

    let notificationBell = {
        count: 0,
        notifications: [],
        isOpen: false,
        updateInterval: null,
    };

    /**
     * Initialize notification system
     */
    function initNotifications() {
        // Load initial notifications
        loadNotificationCount();
        loadRecentNotifications();

        // Setup event listeners
        setupEventListeners();

        // Start auto-refresh (every 30 seconds)
        startAutoRefresh();

        // Listen for dropdown open/close
        const dropdownElement = document.getElementById('notification-dropdown');
        if (dropdownElement) {
            dropdownElement.addEventListener('shown.bs.dropdown', function() {
                notificationBell.isOpen = true;
                loadRecentNotifications();
            });

            dropdownElement.addEventListener('hidden.bs.dropdown', function() {
                notificationBell.isOpen = false;
            });
        }
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Mark all as read button
        const markAllReadBtn = document.getElementById('mark-all-read-btn');
        if (markAllReadBtn) {
            markAllReadBtn.addEventListener('click', markAllAsRead);
        }

        // Notification list click delegation
        const notificationList = document.getElementById('notification-items');
        if (notificationList) {
            notificationList.addEventListener('click', function(e) {
                const notificationItem = e.target.closest('.notification-item');
                if (notificationItem) {
                    handleNotificationClick(notificationItem);
                }

                const deleteBtn = e.target.closest('.notification-delete');
                if (deleteBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    const notificationId = deleteBtn.dataset.id;
                    deleteNotification(notificationId);
                }
            });
        }
    }

    /**
     * Load notification count
     */
    async function loadNotificationCount() {
        try {
            const response = await fetch('/api/notifications/unread-count');
            if (!response.ok) throw new Error('Failed to fetch count');

            const data = await response.json();
            updateNotificationBadge(data.count);
        } catch (error) {
            console.error('Error loading notification count:', error);
        }
    }

    /**
     * Load recent notifications
     */
    async function loadRecentNotifications() {
        try {
            const response = await fetch('/api/notifications/recent?limit=10');
            if (!response.ok) throw new Error('Failed to fetch notifications');

            const data = await response.json();
            if (data.success) {
                notificationBell.notifications = data.notifications;
                renderNotifications(data.notifications);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            showNotificationError();
        }
    }

    /**
     * Update notification badge
     */
    function updateNotificationBadge(count) {
        notificationBell.count = count;
        const badge = document.getElementById('notification-count');
        
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    /**
     * Render notifications in dropdown
     */
    function renderNotifications(notifications) {
        const container = document.getElementById('notification-items');
        const noNotificationsDiv = document.getElementById('no-notifications');

        if (!container) return;

        if (notifications.length === 0) {
            container.innerHTML = '';
            if (noNotificationsDiv) {
                noNotificationsDiv.style.display = 'block';
            }
            return;
        }

        if (noNotificationsDiv) {
            noNotificationsDiv.style.display = 'none';
        }

        container.innerHTML = notifications.map(n => createNotificationHTML(n)).join('');
    }

    /**
     * Create HTML for a single notification
     */
    function createNotificationHTML(notification) {
        const isUnread = !notification.is_read;
        const timeAgo = formatTimeAgo(notification.created_at);
        const iconClass = getNotificationIcon(notification.module);
        const colorClass = getNotificationColor(notification.module);

        return `
            <div class="notification-item ${isUnread ? 'unread' : ''}" 
                 data-id="${notification.id}" 
                 data-url="${notification.action_url || ''}"
                 style="padding:12px 16px;border-bottom:1px solid #f0f0f0;cursor:pointer;transition:background 0.2s;">
                <div class="d-flex gap-2">
                    <div class="flex-shrink-0">
                        <div class="notification-icon bg-${colorClass}-subtle text-${colorClass} rounded-circle d-flex align-items-center justify-content-center"
                             style="width:40px;height:40px;">
                            <i class="bi ${iconClass}"></i>
                        </div>
                    </div>
                    <div class="flex-grow-1 min-w-0">
                        <div class="d-flex align-items-start justify-content-between gap-2">
                            <div class="flex-grow-1">
                                <div class="fw-semibold small text-truncate" style="font-size:0.875rem;">
                                    ${escapeHtml(notification.title)}
                                </div>
                                <div class="text-muted small text-truncate" style="font-size:0.8rem;">
                                    ${escapeHtml(notification.message)}
                                </div>
                                <div class="text-muted" style="font-size:0.7rem;margin-top:4px;">
                                    <i class="bi bi-clock me-1"></i>${timeAgo}
                                </div>
                            </div>
                            <button class="btn btn-link btn-sm p-0 text-muted notification-delete" 
                                    data-id="${notification.id}"
                                    style="font-size:1rem;"
                                    title="Delete">
                                <i class="bi bi-x"></i>
                            </button>
                        </div>
                        ${isUnread ? '<div class="notification-unread-dot position-absolute end-0 top-50 translate-middle-y me-3" style="width:8px;height:8px;background:#0d6efd;border-radius:50%;"></div>' : ''}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Handle notification click
     */
    async function handleNotificationClick(notificationItem) {
        const notificationId = notificationItem.dataset.id;
        const url = notificationItem.dataset.url;

        // Mark as clicked
        try {
            await fetch(`/api/notifications/${notificationId}/clicked`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            // Mark as read visually
            notificationItem.classList.remove('unread');

            // Update badge
            loadNotificationCount();

            // Navigate to URL if provided
            if (url && url !== 'null' && url !== '') {
                window.location.href = url;
            }
        } catch (error) {
            console.error('Error marking notification as clicked:', error);
        }
    }

    /**
     * Mark all as read
     */
    async function markAllAsRead() {
        try {
            const response = await fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                // Update UI
                document.querySelectorAll('.notification-item.unread').forEach(item => {
                    item.classList.remove('unread');
                });

                updateNotificationBadge(0);

                // Show success toast
                showToast('All notifications marked as read', 'success');
            }
        } catch (error) {
            console.error('Error marking all as read:', error);
            showToast('Failed to mark all as read', 'danger');
        }
    }

    /**
     * Delete notification
     */
    async function deleteNotification(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/delete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                // Remove from UI
                const item = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
                if (item) {
                    item.style.transition = 'opacity 0.3s, transform 0.3s';
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(100%)';
                    setTimeout(() => {
                        item.remove();
                        
                        // Check if list is empty
                        const items = document.querySelectorAll('.notification-item');
                        if (items.length === 0) {
                            const noNotificationsDiv = document.getElementById('no-notifications');
                            if (noNotificationsDiv) {
                                noNotificationsDiv.style.display = 'block';
                            }
                        }
                    }, 300);
                }

                // Update count
                loadNotificationCount();
            }
        } catch (error) {
            console.error('Error deleting notification:', error);
        }
    }

    /**
     * Start auto-refresh
     */
    function startAutoRefresh() {
        // Refresh count every 30 seconds
        notificationBell.updateInterval = setInterval(() => {
            loadNotificationCount();
            
            // Refresh list if dropdown is open
            if (notificationBell.isOpen) {
                loadRecentNotifications();
            }
        }, 30000);
    }

    /**
     * Stop auto-refresh
     */
    function stopAutoRefresh() {
        if (notificationBell.updateInterval) {
            clearInterval(notificationBell.updateInterval);
            notificationBell.updateInterval = null;
        }
    }

    /**
     * Get notification icon based on module
     */
    function getNotificationIcon(module) {
        const icons = {
            'attendance': 'bi-clock-fill',
            'leave': 'bi-calendar-x-fill',
            'shift': 'bi-clock-history',
            'payroll': 'bi-cash-stack',
            'company': 'bi-building',
            'reports': 'bi-file-earmark-text',
            'settings': 'bi-gear-fill',
            'foss': 'bi-geo-alt-fill',
            'admin': 'bi-shield-check',
            'system': 'bi-gear-fill',
        };
        return icons[module] || 'bi-bell-fill';
    }

    /**
     * Get notification color based on module
     */
    function getNotificationColor(module) {
        const colors = {
            'attendance': 'info',
            'leave': 'warning',
            'shift': 'info',
            'payroll': 'success',
            'company': 'primary',
            'reports': 'secondary',
            'settings': 'secondary',
            'foss': 'info',
            'admin': 'danger',
            'system': 'secondary',
        };
        return colors[module] || 'primary';
    }

    /**
     * Format time ago
     */
    function formatTimeAgo(dateString) {
        if (!dateString) return 'Just now';

        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'Just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        
        return date.toLocaleDateString();
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show error in notification list
     */
    function showNotificationError() {
        const container = document.getElementById('notification-items');
        if (container) {
            container.innerHTML = `
                <div class="text-center text-danger small py-4">
                    <i class="bi bi-exclamation-circle fs-4 d-block mb-2"></i>
                    Failed to load notifications
                </div>
            `;
        }
    }

    /**
     * Show toast message
     */
    function showToast(message, type = 'info') {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} position-fixed bottom-0 end-0 m-3`;
        toast.style.zIndex = '9999';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Add hover effects
     */
    document.addEventListener('DOMContentLoaded', function() {
        const style = document.createElement('style');
        style.textContent = `
            .notification-item:hover {
                background-color: #f8f9fa !important;
            }
            .notification-item.unread {
                background-color: #e7f3ff;
            }
            .notification-item.unread:hover {
                background-color: #d0e7ff !important;
            }
        `;
        document.head.appendChild(style);
    });

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNotifications);
    } else {
        initNotifications();
    }

    // Expose globally for external updates
    window.notificationBell = {
        refresh: loadRecentNotifications,
        updateCount: loadNotificationCount,
    };

})();
