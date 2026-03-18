/**
 * MultiLangForm Component
 * 
 * Manages multi-language input forms for creating and editing content.
 * Supports English (EN), Uzbek (UZ), and Russian (RU).
 * 
 * Features:
 * - Input fields for all 3 languages (English, Uzbek, Russian)
 * - Clear language labels for each field
 * - Validation to ensure all fields are non-empty
 * - Real-time validation error display
 * - Error removal when field is corrected
 * - Data collection and population methods
 * - Support for both input and textarea field types
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.4, 11.3, 11.4, 11.5, 11.6
 */

class MultiLangForm {
    /**
     * Initialize the MultiLangForm component
     * @param {string} containerId - ID of the container element for the form
     * @param {Object} options - Configuration options
     * @param {string} options.fieldName - Base field name (e.g., 'name' or 'text')
     * @param {string} options.fieldType - Field type ('input' or 'textarea')
     * @param {string} options.label - Label for the field group
     * @param {number} options.maxLength - Maximum character length (optional)
     * @param {boolean} options.required - Whether fields are required (default: true)
     */
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            fieldName: options.fieldName || 'name',
            fieldType: options.fieldType || 'input',
            label: options.label || 'Name',
            maxLength: options.maxLength || null,
            required: options.required !== false
        };
        
        // Language configuration in display order
        this.languages = [
            { code: 'en', label: 'English', placeholder: 'Enter in English' },
            { code: 'uz', label: 'Uzbek (O\'zbekcha)', placeholder: 'O\'zbekcha kiriting' },
            { code: 'ru', label: 'Russian (Русский)', placeholder: 'Введите на русском' }
        ];
        
        this.errors = {}; // Track errors by language code
        this.listeners = {
            fieldChanged: [],
            validationError: [],
            validationSuccess: []
        };
        
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Render the multi-language form fields
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID "${this.containerId}" not found`);
            return;
        }
        
        const html = `
            <div class="multilang-form-component space-y-4">
                ${this.languages.map(lang => this.renderField(lang)).join('')}
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * Render a single language field
     * @param {Object} lang - Language configuration object
     * @returns {string} HTML string for the field
     */
    renderField(lang) {
        const fieldId = `${this.options.fieldName}_${lang.code}`;
        const isTextarea = this.options.fieldType === 'textarea';
        const maxLengthAttr = this.options.maxLength ? `maxlength="${this.options.maxLength}"` : '';
        const requiredMark = this.options.required ? '<span class="text-red-500">*</span>' : '';
        
        const inputClasses = `
            w-full px-3 py-2 border border-gray-300 rounded-md 
            focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
            transition-colors duration-200
        `.trim();
        
        const errorClasses = `
            border-red-300 focus:ring-red-500
        `.trim();
        
        const fieldElement = isTextarea 
            ? `<textarea 
                id="${fieldId}" 
                name="${fieldId}"
                class="${inputClasses}"
                placeholder="${lang.placeholder}"
                rows="4"
                ${maxLengthAttr}
                aria-label="${this.options.label} in ${lang.label}"
                aria-required="${this.options.required}"
                aria-invalid="false"
            ></textarea>`
            : `<input 
                type="text" 
                id="${fieldId}" 
                name="${fieldId}"
                class="${inputClasses}"
                placeholder="${lang.placeholder}"
                ${maxLengthAttr}
                aria-label="${this.options.label} in ${lang.label}"
                aria-required="${this.options.required}"
                aria-invalid="false"
            />`;
        
        return `
            <div class="multilang-field" data-lang="${lang.code}">
                <label for="${fieldId}" class="block text-sm font-medium text-gray-700 mb-1">
                    ${lang.label} ${requiredMark}
                </label>
                ${fieldElement}
                <div id="${fieldId}-error" class="hidden mt-1 text-sm text-red-600 flex items-center" role="alert">
                    <svg class="h-4 w-4 mr-1 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                    <span class="error-message"></span>
                </div>
            </div>
        `;
    }
    
    /**
     * Attach event listeners to form fields
     */
    attachEventListeners() {
        this.languages.forEach(lang => {
            const fieldId = `${this.options.fieldName}_${lang.code}`;
            const field = document.getElementById(fieldId);
            
            if (field) {
                // Real-time validation on input
                field.addEventListener('input', () => {
                    this.validateField(lang.code);
                    this.emit('fieldChanged', { language: lang.code, value: field.value.trim() });
                });
                
                // Validation on blur
                field.addEventListener('blur', () => {
                    this.validateField(lang.code);
                });
            }
        });
    }
    
    /**
     * Validate a specific language field
     * @param {string} langCode - Language code to validate
     * @returns {boolean} True if valid, false otherwise
     */
    validateField(langCode) {
        const fieldId = `${this.options.fieldName}_${langCode}`;
        const field = document.getElementById(fieldId);
        
        if (!field) return true;
        
        const value = field.value.trim();
        const isValid = !this.options.required || value.length > 0;
        
        if (isValid) {
            this.clearFieldError(langCode);
            return true;
        } else {
            const lang = this.languages.find(l => l.code === langCode);
            this.showFieldError(langCode, `${lang.label} is required`);
            return false;
        }
    }
    
    /**
     * Validate all language fields
     * @returns {Object} Validation result with valid flag and errors object
     */
    validate() {
        let isValid = true;
        const errors = {};
        
        this.languages.forEach(lang => {
            const fieldValid = this.validateField(lang.code);
            if (!fieldValid) {
                isValid = false;
                errors[lang.code] = `${lang.label} is required`;
            }
        });
        
        if (isValid) {
            this.emit('validationSuccess', {});
        } else {
            this.emit('validationError', { errors });
        }
        
        return {
            valid: isValid,
            errors
        };
    }
    
    /**
     * Show error for a specific field
     * @param {string} langCode - Language code
     * @param {string} message - Error message to display
     */
    showFieldError(langCode, message) {
        const fieldId = `${this.options.fieldName}_${langCode}`;
        const field = document.getElementById(fieldId);
        const errorDiv = document.getElementById(`${fieldId}-error`);
        
        if (!field || !errorDiv) return;
        
        // Update error state
        this.errors[langCode] = message;
        
        // Update field styling
        field.classList.add('border-red-300');
        field.classList.remove('border-gray-300');
        field.setAttribute('aria-invalid', 'true');
        
        // Show error message
        const errorMessage = errorDiv.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.textContent = message;
        }
        errorDiv.classList.remove('hidden');
    }
    
    /**
     * Clear error for a specific field
     * @param {string} langCode - Language code
     */
    clearFieldError(langCode) {
        const fieldId = `${this.options.fieldName}_${langCode}`;
        const field = document.getElementById(fieldId);
        const errorDiv = document.getElementById(`${fieldId}-error`);
        
        if (!field || !errorDiv) return;
        
        // Clear error state
        delete this.errors[langCode];
        
        // Update field styling
        field.classList.remove('border-red-300');
        field.classList.add('border-gray-300');
        field.setAttribute('aria-invalid', 'false');
        
        // Hide error message
        errorDiv.classList.add('hidden');
    }
    
    /**
     * Clear all errors
     */
    clearErrors() {
        this.languages.forEach(lang => {
            this.clearFieldError(lang.code);
        });
        this.errors = {};
    }
    
    /**
     * Get data from all language fields
     * @returns {Object} Object with keys like name_en, name_uz, name_ru
     */
    getData() {
        const data = {};
        
        this.languages.forEach(lang => {
            const fieldId = `${this.options.fieldName}_${lang.code}`;
            const field = document.getElementById(fieldId);
            
            if (field) {
                data[`${this.options.fieldName}_${lang.code}`] = field.value.trim();
            }
        });
        
        return data;
    }
    
    /**
     * Set data to all language fields
     * @param {Object} data - Object with keys like name_en, name_uz, name_ru
     */
    setData(data) {
        if (!data) return;
        
        this.languages.forEach(lang => {
            const fieldId = `${this.options.fieldName}_${lang.code}`;
            const field = document.getElementById(fieldId);
            const key = `${this.options.fieldName}_${lang.code}`;
            
            if (field && data[key] !== undefined) {
                field.value = data[key] || '';
            }
        });
        
        // Clear any existing errors
        this.clearErrors();
    }
    
    /**
     * Clear all field values
     */
    clear() {
        this.languages.forEach(lang => {
            const fieldId = `${this.options.fieldName}_${lang.code}`;
            const field = document.getElementById(fieldId);
            
            if (field) {
                field.value = '';
            }
        });
        
        this.clearErrors();
    }
    
    /**
     * Check if form has any errors
     * @returns {boolean} True if there are errors, false otherwise
     */
    hasErrors() {
        return Object.keys(this.errors).length > 0;
    }
    
    /**
     * Get current errors
     * @returns {Object} Object with error messages by language code
     */
    getErrors() {
        return { ...this.errors };
    }
    
    /**
     * Enable all fields
     */
    enable() {
        this.languages.forEach(lang => {
            const fieldId = `${this.options.fieldName}_${lang.code}`;
            const field = document.getElementById(fieldId);
            
            if (field) {
                field.disabled = false;
            }
        });
    }
    
    /**
     * Disable all fields
     */
    disable() {
        this.languages.forEach(lang => {
            const fieldId = `${this.options.fieldName}_${lang.code}`;
            const field = document.getElementById(fieldId);
            
            if (field) {
                field.disabled = true;
            }
        });
    }
    
    /**
     * Register an event listener
     * @param {string} event - Event name (fieldChanged, validationError, validationSuccess)
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
     * @param {*} data - Data to pass to listeners
     */
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MultiLangForm;
}
