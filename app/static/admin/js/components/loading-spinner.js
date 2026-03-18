/**
 * LoadingSpinner Component
 * 
 * Provides visual feedback during asynchronous operations.
 * Supports multiple loading states: skeleton screens, button spinners, and overlay spinners.
 * 
 * Features:
 * - Skeleton screens for initial page load
 * - Button spinners for form submissions
 * - Full-page overlay spinner for long operations
 * - Accessible with ARIA attributes
 * - Non-blocking UI feedback
 * - Smooth animations
 * 
 * Requirements: 12.1, 12.2, 12.3
 */

class LoadingSpinner {
    /**
     * Initialize the LoadingSpinner component (singleton)
     */
    constructor() {
        if (LoadingSpinner.instance) {
            return LoadingSpinner.instance;
        }
        
        this.activeSkeletons = new Map();
        this.activeButtons = new Map();
        this.overlay = null;
        
        LoadingSpinner.instance = this;
    }
    
    /**
     * Show skeleton screen in a container
     * @param {string} containerId - ID of container element
     * @param {Object} options - Configuration options
     * @param {number} options.rows - Number of skeleton rows (default: 3)
     * @param {string} options.type - Skeleton type: 'list', 'card', 'form' (default: 'list')
     */
    showSkeleton(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID "${containerId}" not found`);
            return;
        }
        
        const config = {
            rows: options.rows || 3,
            type: options.type || 'list'
        };
        
        // Store original content
        if (!this.activeSkeletons.has(containerId)) {
            this.activeSkeletons.set(containerId, {
                originalContent: container.innerHTML,
                originalDisplay: container.style.display
            });
        }
        
        // Create skeleton based on type
        const skeleton = this.createSkeleton(config);
        
        // Replace content with skeleton
        container.innerHTML = '';
        container.appendChild(skeleton);
        container.setAttribute('aria-busy', 'true');
        container.setAttribute('aria-live', 'polite');
    }
    
    /**
     * Hide skeleton screen and restore original content
     * @param {string} containerId - ID of container element
     */
    hideSkeleton(containerId) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID "${containerId}" not found`);
            return;
        }
        
        const stored = this.activeSkeletons.get(containerId);
        if (!stored) {
            return;
        }
        
        // Restore original content
        container.innerHTML = stored.originalContent;
        container.style.display = stored.originalDisplay;
        container.removeAttribute('aria-busy');
        
        // Remove from active skeletons
        this.activeSkeletons.delete(containerId);
    }
    
    /**
     * Create skeleton element based on type
     * @param {Object} config - Skeleton configuration
     * @returns {HTMLElement} Skeleton element
     */
    createSkeleton(config) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-container animate-pulse';
        
        switch (config.type) {
            case 'list':
                skeleton.innerHTML = this.createListSkeleton(config.rows);
                break;
            case 'card':
                skeleton.innerHTML = this.createCardSkeleton(config.rows);
                break;
            case 'form':
                skeleton.innerHTML = this.createFormSkeleton(config.rows);
                break;
            default:
                skeleton.innerHTML = this.createListSkeleton(config.rows);
        }
        
        return skeleton;
    }
    
    /**
     * Create list-style skeleton
     * @param {number} rows - Number of rows
     * @returns {string} HTML string
     */
    createListSkeleton(rows) {
        let html = '<div class="space-y-3">';
        
        for (let i = 0; i < rows; i++) {
            html += `
                <div class="flex items-center space-x-4 p-4 bg-white rounded-lg border border-gray-200">
                    <div class="flex-shrink-0 h-12 w-12 bg-gray-200 rounded"></div>
                    <div class="flex-1 space-y-2">
                        <div class="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div class="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Create card-style skeleton
     * @param {number} rows - Number of cards
     * @returns {string} HTML string
     */
    createCardSkeleton(rows) {
        let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">';
        
        for (let i = 0; i < rows; i++) {
            html += `
                <div class="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
                    <div class="h-32 bg-gray-200 rounded"></div>
                    <div class="h-4 bg-gray-200 rounded w-3/4"></div>
                    <div class="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Create form-style skeleton
     * @param {number} rows - Number of form fields
     * @returns {string} HTML string
     */
    createFormSkeleton(rows) {
        let html = '<div class="space-y-4">';
        
        for (let i = 0; i < rows; i++) {
            html += `
                <div class="space-y-2">
                    <div class="h-4 bg-gray-200 rounded w-1/4"></div>
                    <div class="h-10 bg-gray-200 rounded w-full"></div>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    /**
     * Show spinner on a button
     * @param {string} buttonId - ID of button element
     * @param {Object} options - Configuration options
     * @param {string} options.text - Loading text to display (optional)
     */
    showButtonSpinner(buttonId, options = {}) {
        const button = document.getElementById(buttonId);
        if (!button) {
            console.error(`Button with ID "${buttonId}" not found`);
            return;
        }
        
        // Store original button state
        if (!this.activeButtons.has(buttonId)) {
            this.activeButtons.set(buttonId, {
                originalContent: button.innerHTML,
                originalDisabled: button.disabled
            });
        }
        
        // Disable button
        button.disabled = true;
        button.setAttribute('aria-busy', 'true');
        
        // Create spinner
        const spinner = `
            <span class="inline-flex items-center gap-2">
                <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>${options.text || 'Loading...'}</span>
            </span>
        `;
        
        button.innerHTML = spinner;
    }
    
    /**
     * Hide spinner from button and restore original state
     * @param {string} buttonId - ID of button element
     */
    hideButtonSpinner(buttonId) {
        const button = document.getElementById(buttonId);
        if (!button) {
            console.error(`Button with ID "${buttonId}" not found`);
            return;
        }
        
        const stored = this.activeButtons.get(buttonId);
        if (!stored) {
            return;
        }
        
        // Restore original button state
        button.innerHTML = stored.originalContent;
        button.disabled = stored.originalDisabled;
        button.removeAttribute('aria-busy');
        
        // Remove from active buttons
        this.activeButtons.delete(buttonId);
    }
    
    /**
     * Show full-page loading overlay
     * @param {Object} options - Configuration options
     * @param {string} options.message - Loading message to display (optional)
     */
    showOverlay(options = {}) {
        // Remove existing overlay if present
        this.hideOverlay();
        
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.id = 'loading-overlay';
        this.overlay.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 transition-opacity';
        this.overlay.setAttribute('role', 'alert');
        this.overlay.setAttribute('aria-busy', 'true');
        this.overlay.setAttribute('aria-live', 'assertive');
        
        const message = options.message || 'Loading...';
        
        this.overlay.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl p-6 max-w-sm mx-4 text-center">
                <!-- Spinner -->
                <div class="flex justify-center mb-4">
                    <svg class="animate-spin h-12 w-12 text-blue-600" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                </div>
                
                <!-- Message -->
                <p class="text-gray-800 font-medium">${this.escapeHtml(message)}</p>
            </div>
        `;
        
        // Add to DOM
        document.body.appendChild(this.overlay);
        
        // Trigger fade-in
        setTimeout(() => {
            this.overlay.style.opacity = '1';
        }, 10);
    }
    
    /**
     * Hide full-page loading overlay
     */
    hideOverlay() {
        if (this.overlay && this.overlay.parentNode) {
            // Fade out
            this.overlay.style.opacity = '0';
            
            // Remove from DOM after transition
            setTimeout(() => {
                if (this.overlay && this.overlay.parentNode) {
                    this.overlay.parentNode.removeChild(this.overlay);
                    this.overlay = null;
                }
            }, 300);
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

// Add CSS for animations
(function() {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }
        
        .animate-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes spin {
            from {
                transform: rotate(0deg);
            }
            to {
                transform: rotate(360deg);
            }
        }
        
        .animate-spin {
            animation: spin 1s linear infinite;
        }
        
        #loading-overlay {
            transition: opacity 300ms ease-in-out;
        }
    `;
    document.head.appendChild(style);
})();

// Create singleton instance
const loadingSpinner = new LoadingSpinner();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingSpinner;
}
