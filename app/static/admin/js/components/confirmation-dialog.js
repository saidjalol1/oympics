/**
 * ConfirmationDialog Component
 * 
 * Displays modal confirmation dialogs for destructive actions.
 * Provides clear messaging and cascade deletion warnings.
 * 
 * Features:
 * - Modal overlay with centered dialog
 * - Customizable title, message, and button text
 * - Warning icons for destructive actions
 * - Cascade deletion warnings
 * - Keyboard support (Escape to cancel)
 * - Focus management and accessibility
 * - Event-driven confirm/cancel notifications
 * 
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
 */

class ConfirmationDialog {
    /**
     * Initialize the ConfirmationDialog component
     * @param {Object} options - Configuration options
     * @param {string} options.title - Dialog title (default: "Confirm Action")
     * @param {string} options.message - Main message to display
     * @param {string} options.confirmText - Confirm button text (default: "Confirm")
     * @param {string} options.cancelText - Cancel button text (default: "Cancel")
     * @param {string} options.type - Dialog type: 'delete', 'warning', 'info' (default: 'warning')
     * @param {string} options.cascadeWarning - Optional cascade deletion warning message
     */
    constructor(options = {}) {
        this.options = {
            title: options.title || 'Confirm Action',
            message: options.message || 'Are you sure you want to proceed?',
            confirmText: options.confirmText || 'Confirm',
            cancelText: options.cancelText || 'Cancel',
            type: options.type || 'warning',
            cascadeWarning: options.cascadeWarning || null
        };
        
        this.listeners = {
            confirm: [],
            cancel: []
        };
        
        this.dialogElement = null;
        this.previousFocus = null;
    }
    
    /**
     * Show the confirmation dialog
     */
    show() {
        // Store currently focused element to restore later
        this.previousFocus = document.activeElement;
        
        // Create and render dialog
        this.render();
        this.attachEventListeners();
        
        // Add to DOM
        document.body.appendChild(this.dialogElement);
        
        // Focus the confirm button
        setTimeout(() => {
            const confirmButton = this.dialogElement.querySelector('#confirm-button');
            if (confirmButton) {
                confirmButton.focus();
            }
        }, 100);
    }
    
    /**
     * Hide the confirmation dialog
     */
    hide() {
        if (this.dialogElement && this.dialogElement.parentNode) {
            // Restore focus to previous element
            if (this.previousFocus && typeof this.previousFocus.focus === 'function') {
                this.previousFocus.focus();
            }
            
            // Remove from DOM
            this.dialogElement.parentNode.removeChild(this.dialogElement);
            this.dialogElement = null;
        }
    }
    
    /**
     * Render the confirmation dialog
     */
    render() {
        // Create dialog container
        const dialog = document.createElement('div');
        dialog.className = 'confirmation-dialog-overlay fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 transition-opacity';
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');
        dialog.setAttribute('aria-labelledby', 'dialog-title');
        dialog.setAttribute('aria-describedby', 'dialog-message');
        
        // Get icon and colors based on type
        const { icon, confirmButtonClass } = this.getTypeStyles();
        
        // Build cascade warning HTML if provided
        const cascadeWarningHtml = this.options.cascadeWarning ? `
            <div class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                <div class="flex">
                    <svg class="h-5 w-5 text-yellow-400 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                    </svg>
                    <p class="text-sm text-yellow-800">${this.escapeHtml(this.options.cascadeWarning)}</p>
                </div>
            </div>
        ` : '';
        
        dialog.innerHTML = `
            <div class="confirmation-dialog-content bg-white rounded-lg shadow-xl max-w-md w-full mx-4 transform transition-all">
                <!-- Dialog Header -->
                <div class="px-6 pt-6 pb-4">
                    <div class="flex items-start">
                        <!-- Icon -->
                        <div class="flex-shrink-0">
                            ${icon}
                        </div>
                        
                        <!-- Title and Message -->
                        <div class="ml-4 flex-1">
                            <h3 id="dialog-title" class="text-lg font-medium text-gray-900">
                                ${this.escapeHtml(this.options.title)}
                            </h3>
                            <div id="dialog-message" class="mt-2 text-sm text-gray-600">
                                ${this.escapeHtml(this.options.message)}
                            </div>
                            
                            <!-- Cascade Warning -->
                            ${cascadeWarningHtml}
                        </div>
                    </div>
                </div>
                
                <!-- Dialog Actions -->
                <div class="px-6 py-4 bg-gray-50 rounded-b-lg flex flex-row-reverse gap-3">
                    <button 
                        type="button"
                        id="confirm-button"
                        class="${confirmButtonClass} px-4 py-2 text-sm font-medium text-white rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors"
                    >
                        ${this.escapeHtml(this.options.confirmText)}
                    </button>
                    <button 
                        type="button"
                        id="cancel-button"
                        class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                    >
                        ${this.escapeHtml(this.options.cancelText)}
                    </button>
                </div>
            </div>
        `;
        
        this.dialogElement = dialog;
    }
    
    /**
     * Get icon and button styles based on dialog type
     * @returns {Object} Object with icon HTML and button class
     */
    getTypeStyles() {
        switch (this.options.type) {
            case 'delete':
                return {
                    icon: `
                        <div class="flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                            <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                        </div>
                    `,
                    confirmButtonClass: 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
                };
            
            case 'warning':
                return {
                    icon: `
                        <div class="flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100">
                            <svg class="h-6 w-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                        </div>
                    `,
                    confirmButtonClass: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500'
                };
            
            case 'info':
                return {
                    icon: `
                        <div class="flex items-center justify-center h-12 w-12 rounded-full bg-blue-100">
                            <svg class="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                    `,
                    confirmButtonClass: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
                };
            
            default:
                return {
                    icon: `
                        <div class="flex items-center justify-center h-12 w-12 rounded-full bg-gray-100">
                            <svg class="h-6 w-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                    `,
                    confirmButtonClass: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
                };
        }
    }
    
    /**
     * Attach event listeners to dialog elements
     */
    attachEventListeners() {
        if (!this.dialogElement) return;
        
        const confirmButton = this.dialogElement.querySelector('#confirm-button');
        const cancelButton = this.dialogElement.querySelector('#cancel-button');
        const overlay = this.dialogElement;
        
        // Confirm button
        if (confirmButton) {
            confirmButton.addEventListener('click', () => {
                this.handleConfirm();
            });
        }
        
        // Cancel button
        if (cancelButton) {
            cancelButton.addEventListener('click', () => {
                this.handleCancel();
            });
        }
        
        // Click overlay to cancel
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.handleCancel();
            }
        });
        
        // Escape key to cancel
        this.keydownHandler = (e) => {
            if (e.key === 'Escape') {
                this.handleCancel();
            }
        };
        document.addEventListener('keydown', this.keydownHandler);
        
        // Focus trap
        this.setupFocusTrap();
    }
    
    /**
     * Setup focus trap to keep focus within dialog
     */
    setupFocusTrap() {
        if (!this.dialogElement) return;
        
        const focusableElements = this.dialogElement.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        this.dialogElement.addEventListener('keydown', (e) => {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        });
    }
    
    /**
     * Handle confirm action
     */
    handleConfirm() {
        this.emit('confirm');
        this.cleanup();
        this.hide();
    }
    
    /**
     * Handle cancel action
     */
    handleCancel() {
        this.emit('cancel');
        this.cleanup();
        this.hide();
    }
    
    /**
     * Cleanup event listeners
     */
    cleanup() {
        if (this.keydownHandler) {
            document.removeEventListener('keydown', this.keydownHandler);
            this.keydownHandler = null;
        }
    }
    
    /**
     * Update the dialog message
     * @param {string} message - New message to display
     */
    setMessage(message) {
        this.options.message = message;
        
        if (this.dialogElement) {
            const messageElement = this.dialogElement.querySelector('#dialog-message');
            if (messageElement) {
                messageElement.textContent = message;
            }
        }
    }
    
    /**
     * Update the cascade warning
     * @param {string} warning - New cascade warning message
     */
    setCascadeWarning(warning) {
        this.options.cascadeWarning = warning;
        
        // If dialog is already shown, re-render
        if (this.dialogElement) {
            const isVisible = this.dialogElement.parentNode !== null;
            if (isVisible) {
                this.hide();
                this.show();
            }
        }
    }
    
    /**
     * Register an event listener
     * @param {string} event - Event name (confirm, cancel)
     * @param {Function} callback - Callback function to execute
     */
    on(event, callback) {
        if (this.listeners[event] && typeof callback === 'function') {
            this.listeners[event].push(callback);
        }
    }
    
    /**
     * Emit an event to all registered listeners
     * @param {string} event - Event name
     */
    emit(event) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback();
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConfirmationDialog;
}
