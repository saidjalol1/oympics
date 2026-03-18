/**
 * Notification Component
 * 
 * Displays toast-style notifications for user feedback.
 * Supports multiple notification types with auto-dismiss and manual dismiss options.
 * 
 * Features:
 * - Toast-style notifications in top-right corner
 * - Multiple types: success (green), error (red), warning (yellow), info (blue)
 * - Success notifications auto-dismiss after 3 seconds
 * - Error notifications require manual dismiss
 * - Stack multiple notifications vertically
 * - Smooth slide-in/slide-out animations
 * - Accessible with ARIA attributes
 * - Singleton pattern (one notification manager instance)
 * 
 * Requirements: 12.4, 12.5, 12.6, 12.7
 */

class Notification {
    /**
     * Initialize the Notification component (singleton)
     */
    constructor() {
        if (Notification.instance) {
            return Notification.instance;
        }
        
        this.notifications = [];
        this.nextId = 1;
        this.container = null;
        
        this.init();
        
        Notification.instance = this;
    }
    
    /**
     * Initialize the notification container
     */
    init() {
        // Create container if it doesn't exist
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'fixed top-4 right-4 z-50 flex flex-col gap-3 max-w-md';
            this.container.setAttribute('aria-live', 'polite');
            this.container.setAttribute('aria-atomic', 'false');
            document.body.appendChild(this.container);
        }
    }
    
    /**
     * Show a notification
     * @param {string} message - Message to display
     * @param {string} type - Notification type: 'success', 'error', 'warning', 'info'
     * @param {Object} options - Additional options
     * @param {number} options.duration - Auto-dismiss duration in ms (0 = no auto-dismiss)
     * @param {boolean} options.dismissible - Whether notification can be manually dismissed
     * @returns {number} Notification ID
     */
    show(message, type = 'info', options = {}) {
        const id = this.nextId++;
        
        // Default options based on type
        const defaults = this.getDefaultOptions(type);
        const config = {
            ...defaults,
            ...options,
            id,
            message,
            type
        };
        
        // Create notification element
        const notificationElement = this.createNotificationElement(config);
        
        // Add to container
        this.container.appendChild(notificationElement);
        
        // Store notification
        this.notifications.push({
            id,
            element: notificationElement,
            config
        });
        
        // Trigger slide-in animation
        setTimeout(() => {
            notificationElement.classList.add('notification-show');
        }, 10);
        
        // Auto-dismiss if duration is set
        if (config.duration > 0) {
            setTimeout(() => {
                this.dismiss(id);
            }, config.duration);
        }
        
        return id;
    }
    
    /**
     * Show a success notification
     * @param {string} message - Message to display
     * @param {Object} options - Additional options
     * @returns {number} Notification ID
     */
    success(message, options = {}) {
        return this.show(message, 'success', options);
    }
    
    /**
     * Show an error notification
     * @param {string} message - Message to display
     * @param {Object} options - Additional options
     * @returns {number} Notification ID
     */
    error(message, options = {}) {
        return this.show(message, 'error', options);
    }
    
    /**
     * Show a warning notification
     * @param {string} message - Message to display
     * @param {Object} options - Additional options
     * @returns {number} Notification ID
     */
    warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }
    
    /**
     * Show an info notification
     * @param {string} message - Message to display
     * @param {Object} options - Additional options
     * @returns {number} Notification ID
     */
    info(message, options = {}) {
        return this.show(message, 'info', options);
    }
    
    /**
     * Dismiss a notification
     * @param {number} id - Notification ID to dismiss
     */
    dismiss(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (!notification) return;
        
        // Trigger slide-out animation
        notification.element.classList.remove('notification-show');
        notification.element.classList.add('notification-hide');
        
        // Remove from DOM after animation
        setTimeout(() => {
            if (notification.element.parentNode) {
                notification.element.parentNode.removeChild(notification.element);
            }
            
            // Remove from array
            this.notifications = this.notifications.filter(n => n.id !== id);
        }, 300);
    }
    
    /**
     * Dismiss all notifications
     */
    dismissAll() {
        const ids = this.notifications.map(n => n.id);
        ids.forEach(id => this.dismiss(id));
    }
    
    /**
     * Get default options for notification type
     * @param {string} type - Notification type
     * @returns {Object} Default options
     */
    getDefaultOptions(type) {
        switch (type) {
            case 'success':
                return {
                    duration: 3000, // Auto-dismiss after 3 seconds
                    dismissible: true
                };
            case 'error':
                return {
                    duration: 0, // No auto-dismiss
                    dismissible: true // Manual dismiss required
                };
            case 'warning':
                return {
                    duration: 5000,
                    dismissible: true
                };
            case 'info':
                return {
                    duration: 4000,
                    dismissible: true
                };
            default:
                return {
                    duration: 3000,
                    dismissible: true
                };
        }
    }
    
    /**
     * Create notification element
     * @param {Object} config - Notification configuration
     * @returns {HTMLElement} Notification element
     */
    createNotificationElement(config) {
        const { id, message, type, dismissible } = config;
        
        // Get styles based on type
        const styles = this.getTypeStyles(type);
        
        // Create notification element
        const notification = document.createElement('div');
        notification.id = `notification-${id}`;
        notification.className = `notification bg-white rounded-lg shadow-lg border-l-4 ${styles.borderColor} p-4 flex items-start gap-3 transform transition-all duration-300 translate-x-full opacity-0`;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
        
        // Icon
        const iconContainer = document.createElement('div');
        iconContainer.className = 'flex-shrink-0';
        iconContainer.innerHTML = styles.icon;
        
        // Message
        const messageContainer = document.createElement('div');
        messageContainer.className = 'flex-1 text-sm text-gray-800';
        messageContainer.textContent = message;
        
        // Dismiss button
        let dismissButton = null;
        if (dismissible) {
            dismissButton = document.createElement('button');
            dismissButton.type = 'button';
            dismissButton.className = 'flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 rounded transition-colors';
            dismissButton.setAttribute('aria-label', 'Dismiss notification');
            dismissButton.innerHTML = `
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            `;
            dismissButton.addEventListener('click', () => {
                this.dismiss(id);
            });
        }
        
        // Assemble notification
        notification.appendChild(iconContainer);
        notification.appendChild(messageContainer);
        if (dismissButton) {
            notification.appendChild(dismissButton);
        }
        
        return notification;
    }
    
    /**
     * Get icon and styles based on notification type
     * @param {string} type - Notification type
     * @returns {Object} Object with icon HTML and border color
     */
    getTypeStyles(type) {
        switch (type) {
            case 'success':
                return {
                    icon: `
                        <div class="flex items-center justify-center h-6 w-6 rounded-full bg-green-100">
                            <svg class="h-4 w-4 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    `,
                    borderColor: 'border-green-500'
                };
            
            case 'error':
                return {
                    icon: `
                        <div class="flex items-center justify-center h-6 w-6 rounded-full bg-red-100">
                            <svg class="h-4 w-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    `,
                    borderColor: 'border-red-500'
                };
            
            case 'warning':
                return {
                    icon: `
                        <div class="flex items-center justify-center h-6 w-6 rounded-full bg-yellow-100">
                            <svg class="h-4 w-4 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    `,
                    borderColor: 'border-yellow-500'
                };
            
            case 'info':
                return {
                    icon: `
                        <div class="flex items-center justify-center h-6 w-6 rounded-full bg-blue-100">
                            <svg class="h-4 w-4 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    `,
                    borderColor: 'border-blue-500'
                };
            
            default:
                return {
                    icon: `
                        <div class="flex items-center justify-center h-6 w-6 rounded-full bg-gray-100">
                            <svg class="h-4 w-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                            </svg>
                        </div>
                    `,
                    borderColor: 'border-gray-500'
                };
        }
    }
}

// Add CSS for animations
(function() {
    const style = document.createElement('style');
    style.textContent = `
        .notification-show {
            transform: translateX(0) !important;
            opacity: 1 !important;
        }
        
        .notification-hide {
            transform: translateX(100%) !important;
            opacity: 0 !important;
        }
    `;
    document.head.appendChild(style);
})();

// Create singleton instance
const notificationManager = new Notification();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Notification;
}
