/**
 * Validation Utility
 * 
 * Provides frontend validation that mirrors backend validation rules.
 * 
 * Features:
 * - Translation field validation (all 3 languages required)
 * - Image file validation (size, format, dimensions)
 * - Price validation (>= 0, decimal with 2 places)
 * - Consistent validation with backend
 * 
 * Requirements: 30.1, 30.3, 30.4, 30.6, 30.7
 */

const Validation = {
    /**
     * Supported languages
     */
    SUPPORTED_LANGUAGES: ['en', 'uz', 'ru'],
    
    /**
     * Image validation constants
     */
    IMAGE: {
        MAX_FILE_SIZE: 5242880, // 5MB in bytes
        ALLOWED_FORMATS: ['image/jpeg', 'image/png', 'image/webp'],
        ALLOWED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.webp'],
        MIN_DIMENSION: 100,
        MAX_DIMENSION: 4000,
        MAX_COUNT: 2
    },
    
    /**
     * Price validation constants
     */
    PRICE: {
        MIN: 0,
        MAX: 99999999.99,
        DECIMAL_PLACES: 2
    },
    
    /**
     * Validate translation fields
     * Requirement 30.1: All three language fields must be non-empty
     * 
     * @param {Object} translations - Object with en, uz, ru properties
     * @param {string} fieldName - Name of the field being validated (for error messages)
     * @returns {Object} Validation result { valid: boolean, errors: Array }
     */
    validateTranslations(translations, fieldName = 'field') {
        const errors = [];
        
        if (!translations || typeof translations !== 'object') {
            errors.push(`${fieldName} translations must be an object`);
            return { valid: false, errors };
        }
        
        // Check each language
        this.SUPPORTED_LANGUAGES.forEach(lang => {
            const value = translations[lang];
            
            if (!value || typeof value !== 'string' || value.trim() === '') {
                errors.push(`${fieldName} in ${lang.toUpperCase()} is required`);
            }
        });
        
        return {
            valid: errors.length === 0,
            errors
        };
    },
    
    /**
     * Validate a single translation field
     * @param {string} value - Field value
     * @param {string} language - Language code (en, uz, ru)
     * @param {string} fieldName - Name of the field
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateTranslationField(value, language, fieldName = 'field') {
        if (!value || typeof value !== 'string' || value.trim() === '') {
            return {
                valid: false,
                error: `${fieldName} in ${language.toUpperCase()} is required`
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate image file
     * Requirement 30.3: Image size, format, and dimension validation
     * 
     * @param {File} file - Image file to validate
     * @returns {Promise<Object>} Validation result { valid: boolean, error: string|null }
     */
    async validateImageFile(file) {
        // Check if file exists
        if (!file) {
            return { valid: false, error: 'No file provided' };
        }
        
        // Validate file size
        if (file.size === 0) {
            return { valid: false, error: 'File is empty' };
        }
        
        if (file.size > this.IMAGE.MAX_FILE_SIZE) {
            const maxSizeMB = (this.IMAGE.MAX_FILE_SIZE / 1024 / 1024).toFixed(1);
            return {
                valid: false,
                error: `File size exceeds ${maxSizeMB}MB limit`
            };
        }
        
        // Validate file format by MIME type
        if (!this.IMAGE.ALLOWED_FORMATS.includes(file.type)) {
            return {
                valid: false,
                error: 'Unsupported format. Allowed: JPEG, PNG, WebP'
            };
        }
        
        // Validate file extension
        const extension = this.getFileExtension(file.name);
        if (!this.IMAGE.ALLOWED_EXTENSIONS.includes(extension)) {
            return {
                valid: false,
                error: 'Unsupported file extension. Allowed: .jpg, .jpeg, .png, .webp'
            };
        }
        
        // Validate image dimensions
        try {
            const dimensions = await this.getImageDimensions(file);
            
            if (dimensions.width < this.IMAGE.MIN_DIMENSION || 
                dimensions.height < this.IMAGE.MIN_DIMENSION) {
                return {
                    valid: false,
                    error: `Image must be at least ${this.IMAGE.MIN_DIMENSION}x${this.IMAGE.MIN_DIMENSION} pixels`
                };
            }
            
            if (dimensions.width > this.IMAGE.MAX_DIMENSION || 
                dimensions.height > this.IMAGE.MAX_DIMENSION) {
                return {
                    valid: false,
                    error: `Image must not exceed ${this.IMAGE.MAX_DIMENSION}x${this.IMAGE.MAX_DIMENSION} pixels`
                };
            }
            
            return { valid: true, error: null, dimensions };
        } catch (error) {
            return {
                valid: false,
                error: 'Invalid image file or unable to read dimensions'
            };
        }
    },
    
    /**
     * Get image dimensions by loading it in the browser
     * @param {File} file - Image file
     * @returns {Promise<Object>} Object with width and height
     */
    getImageDimensions(file) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            const url = URL.createObjectURL(file);
            
            img.onload = () => {
                URL.revokeObjectURL(url);
                resolve({
                    width: img.width,
                    height: img.height
                });
            };
            
            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('Failed to load image'));
            };
            
            img.src = url;
        });
    },
    
    /**
     * Get file extension from filename
     * @param {string} filename - File name
     * @returns {string} File extension (lowercase, with dot)
     */
    getFileExtension(filename) {
        const lastDot = filename.lastIndexOf('.');
        if (lastDot === -1) return '';
        return filename.substring(lastDot).toLowerCase();
    },
    
    /**
     * Validate image count
     * @param {number} count - Number of images
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateImageCount(count) {
        if (count > this.IMAGE.MAX_COUNT) {
            return {
                valid: false,
                error: `Maximum of ${this.IMAGE.MAX_COUNT} images allowed`
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate price value
     * Requirement 30.4: Price >= 0, decimal with 2 places
     * 
     * @param {string|number} price - Price value to validate
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validatePrice(price) {
        // Allow empty/null for optional fields
        if (price === null || price === undefined || price === '') {
            return { valid: true, error: null };
        }
        
        // Convert to number
        const numPrice = typeof price === 'string' ? parseFloat(price) : price;
        
        // Check if valid number
        if (isNaN(numPrice)) {
            return {
                valid: false,
                error: 'Price must be a valid number'
            };
        }
        
        // Check minimum value
        if (numPrice < this.PRICE.MIN) {
            return {
                valid: false,
                error: `Price must be greater than or equal to ${this.PRICE.MIN}`
            };
        }
        
        // Check maximum value
        if (numPrice > this.PRICE.MAX) {
            return {
                valid: false,
                error: `Price must not exceed ${this.PRICE.MAX}`
            };
        }
        
        // Check decimal places
        const decimalPlaces = this.getDecimalPlaces(numPrice);
        if (decimalPlaces > this.PRICE.DECIMAL_PLACES) {
            return {
                valid: false,
                error: `Price must have at most ${this.PRICE.DECIMAL_PLACES} decimal places`
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Get number of decimal places in a number
     * @param {number} num - Number to check
     * @returns {number} Number of decimal places
     */
    getDecimalPlaces(num) {
        const str = num.toString();
        const decimalIndex = str.indexOf('.');
        
        if (decimalIndex === -1) return 0;
        
        return str.length - decimalIndex - 1;
    },
    
    /**
     * Format price for display
     * @param {number} price - Price value
     * @param {string} currency - Currency symbol (default: '$')
     * @returns {string} Formatted price
     */
    formatPrice(price, currency = '$') {
        if (price === 0 || price === '0' || price === '0.00') {
            return 'Free';
        }
        
        const numPrice = typeof price === 'string' ? parseFloat(price) : price;
        return `${currency}${numPrice.toFixed(2)}`;
    },
    
    /**
     * Validate correct answer (A-J)
     * @param {string} answer - Answer value
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateCorrectAnswer(answer) {
        if (!answer || typeof answer !== 'string') {
            return {
                valid: false,
                error: 'Correct answer is required'
            };
        }
        
        const validAnswers = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
        if (!validAnswers.includes(answer.toUpperCase())) {
            return {
                valid: false,
                error: 'Correct answer must be between A and J'
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate option label (A-J)
     * @param {string} label - Option label
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateOptionLabel(label) {
        if (!label || typeof label !== 'string') {
            return {
                valid: false,
                error: 'Option label is required'
            };
        }
        
        const validLabels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
        if (!validLabels.includes(label.toUpperCase())) {
            return {
                valid: false,
                error: 'Option label must be between A and J'
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate email address
     * @param {string} email - Email address
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateEmail(email) {
        if (!email || typeof email !== 'string') {
            return {
                valid: false,
                error: 'Email is required'
            };
        }
        
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return {
                valid: false,
                error: 'Invalid email address'
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate required field
     * @param {any} value - Field value
     * @param {string} fieldName - Name of the field
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateRequired(value, fieldName = 'Field') {
        if (value === null || value === undefined || 
            (typeof value === 'string' && value.trim() === '')) {
            return {
                valid: false,
                error: `${fieldName} is required`
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate string length
     * @param {string} value - String value
     * @param {number} minLength - Minimum length
     * @param {number} maxLength - Maximum length
     * @param {string} fieldName - Name of the field
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateLength(value, minLength, maxLength, fieldName = 'Field') {
        if (!value || typeof value !== 'string') {
            return { valid: true, error: null }; // Let validateRequired handle this
        }
        
        if (value.length < minLength) {
            return {
                valid: false,
                error: `${fieldName} must be at least ${minLength} characters`
            };
        }
        
        if (value.length > maxLength) {
            return {
                valid: false,
                error: `${fieldName} must not exceed ${maxLength} characters`
            };
        }
        
        return { valid: true, error: null };
    },
    
    /**
     * Validate date range
     * @param {Date|string} startDate - Start date
     * @param {Date|string} endDate - End date
     * @returns {Object} Validation result { valid: boolean, error: string|null }
     */
    validateDateRange(startDate, endDate) {
        if (!startDate || !endDate) {
            return { valid: true, error: null }; // Optional dates
        }
        
        const start = new Date(startDate);
        const end = new Date(endDate);
        
        if (isNaN(start.getTime()) || isNaN(end.getTime())) {
            return {
                valid: false,
                error: 'Invalid date format'
            };
        }
        
        if (end < start) {
            return {
                valid: false,
                error: 'End date must be after start date'
            };
        }
        
        return { valid: true, error: null };
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Validation;
}
