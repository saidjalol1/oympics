/**
 * UI Utilities Module
 * Handles all UI interactions and display logic
 */

const UIUtils = {
    // Modal Management
    openModal(modalId) {
        document.getElementById(modalId).classList.remove('hidden');
    },

    closeModal(modalId) {
        document.getElementById(modalId).classList.add('hidden');
    },

    // Toast Notifications
    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        const bgColor = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500'
        }[type] || 'bg-blue-500';

        toast.className = `${bgColor} text-white px-4 py-3 rounded-md shadow-lg text-sm pointer-events-auto`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    },

    // Loading States
    showLoading() {
        document.getElementById('loading-state').classList.remove('hidden');
        document.getElementById('table-container').classList.add('hidden');
        document.getElementById('empty-state').classList.add('hidden');
        document.getElementById('error-state').classList.add('hidden');
        document.getElementById('pagination-container').classList.add('hidden');
    },

    hideLoading() {
        document.getElementById('loading-state').classList.add('hidden');
    },

    showError(message) {
        this.hideLoading();
        document.getElementById('error-message').textContent = message;
        document.getElementById('error-state').classList.remove('hidden');
        document.getElementById('table-container').classList.add('hidden');
        document.getElementById('empty-state').classList.add('hidden');
        document.getElementById('pagination-container').classList.add('hidden');
    },

    showEmpty() {
        this.hideLoading();
        document.getElementById('error-state').classList.add('hidden');
        document.getElementById('table-container').classList.add('hidden');
        document.getElementById('empty-state').classList.remove('hidden');
        document.getElementById('pagination-container').classList.add('hidden');
    },

    showTable() {
        this.hideLoading();
        document.getElementById('error-state').classList.add('hidden');
        document.getElementById('table-container').classList.remove('hidden');
        document.getElementById('pagination-container').classList.remove('hidden');
    },

    // Date Formatting
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    // Error Parsing
    parseError(error) {
        // Handle error object from API client
        if (error && typeof error === 'object') {
            // Check for message field
            if (error.message) {
                return error.message;
            }
            
            // Check for data.detail field
            if (error.data && error.data.detail) {
                if (typeof error.data.detail === 'string') {
                    return error.data.detail;
                }
                if (Array.isArray(error.data.detail)) {
                    return error.data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ');
                }
            }
            
            // Check for data.message field
            if (error.data && error.data.message) {
                return error.data.message;
            }
            
            // Check for statusText
            if (error.statusText) {
                return error.statusText;
            }
        }
        
        // Handle string errors
        if (typeof error === 'string') {
            return error;
        }
        
        return 'An error occurred';
    }
};
