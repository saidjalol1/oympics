/**
 * LanguageSwitcher Component
 * 
 * Manages language selection and UI updates for multi-language support.
 * Supports English (EN), Uzbek (UZ), and Russian (RU).
 * 
 * Features:
 * - Language dropdown selector
 * - localStorage persistence
 * - Event-driven language change notifications
 * - Automatic UI text updates via data-i18n attributes
 * - Fallback to English for missing translations
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4
 */

class LanguageSwitcher {
    /**
     * Initialize the LanguageSwitcher component
     * @param {string} containerId - ID of the container element for the language switcher
     * @param {Object} translations - Translation object with structure: { en: {}, uz: {}, ru: {} }
     */
    constructor(containerId, translations = {}) {
        this.containerId = containerId;
        this.translations = translations;
        
        // Supported languages - MUST be defined before loadLanguage() is called
        this.languages = {
            en: 'English',
            uz: 'O\'zbekcha',
            ru: 'Русский'
        };
        
        this.currentLanguage = this.loadLanguage();
        this.listeners = {
            languageChanged: []
        };
        
        this.render();
        this.attachEventListeners();
        
        // Initial UI update (only if translations are provided)
        if (this.translations && Object.keys(this.translations).length > 0) {
            try {
                this.updateUI();
            } catch (error) {
                console.warn('Error during initial UI update:', error);
            }
        }
    }
    
    /**
     * Render the language switcher dropdown
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID "${this.containerId}" not found`);
            return;
        }
        
        const html = `
            <div class="language-switcher">
                <select 
                    id="language-select" 
                    class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                    aria-label="Select language"
                >
                    ${Object.entries(this.languages).map(([code, name]) => `
                        <option value="${code}" ${code === this.currentLanguage ? 'selected' : ''}>
                            ${name}
                        </option>
                    `).join('')}
                </select>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * Attach event listeners to the language selector
     */
    attachEventListeners() {
        const select = document.getElementById('language-select');
        if (select) {
            select.addEventListener('change', (e) => {
                this.setLanguage(e.target.value);
            });
        }
    }
    
    /**
     * Get the current selected language
     * @returns {string} Current language code (en, uz, or ru)
     */
    getCurrentLanguage() {
        return this.currentLanguage;
    }
    
    /**
     * Set the current language and update UI
     * @param {string} languageCode - Language code to set (en, uz, or ru)
     */
    setLanguage(languageCode) {
        if (!this.languages[languageCode]) {
            console.error(`Invalid language code: ${languageCode}`);
            return;
        }
        
        const startTime = performance.now();
        
        this.currentLanguage = languageCode;
        this.saveLanguage(languageCode);
        this.updateUI();
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        // Requirement 2.2: Update UI within 200ms
        if (duration > 200) {
            console.warn(`Language switch took ${duration.toFixed(2)}ms (exceeds 200ms requirement)`);
        }
        
        // Emit language changed event
        this.emit('languageChanged', { language: languageCode, duration });
    }
    
    /**
     * Load language preference from localStorage
     * @returns {string} Saved language code or default 'en'
     */
    loadLanguage() {
        try {
            const saved = localStorage.getItem('preferred_language');
            if (saved && this.languages[saved]) {
                return saved;
            }
        } catch (error) {
            console.error('Error loading language preference:', error);
        }
        return 'en'; // Default to English
    }
    
    /**
     * Save language preference to localStorage
     * @param {string} languageCode - Language code to save
     */
    saveLanguage(languageCode) {
        try {
            localStorage.setItem('preferred_language', languageCode);
        } catch (error) {
            console.error('Error saving language preference:', error);
        }
    }
    
    /**
     * Update all UI elements with data-i18n attributes
     * Requirement 2.5: Display entity content in currently selected UI_Language
     * Requirement 2.6: Fallback to English for missing translations
     */
    updateUI() {
        const elements = document.querySelectorAll('[data-i18n]');
        
        elements.forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.getTranslation(key);
            
            if (translation) {
                // Update text content or placeholder based on element type
                if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                    if (element.hasAttribute('placeholder')) {
                        element.placeholder = translation;
                    } else {
                        element.value = translation;
                    }
                } else {
                    element.textContent = translation;
                }
            }
        });
    }
    
    /**
     * Get translation for a key in the current language
     * Falls back to English if translation is missing
     * @param {string} key - Translation key
     * @returns {string|null} Translated text or null if not found
     */
    getTranslation(key) {
        // Guard against undefined translations
        if (!this.translations || typeof this.translations !== 'object') {
            console.warn('Translations object is not initialized');
            return null;
        }
        
        // Try current language
        if (this.translations[this.currentLanguage] && 
            this.translations[this.currentLanguage][key]) {
            return this.translations[this.currentLanguage][key];
        }
        
        // Fallback to English
        if (this.currentLanguage !== 'en' && 
            this.translations.en && 
            this.translations.en[key]) {
            console.warn(`Translation missing for key "${key}" in ${this.currentLanguage}, using English fallback`);
            return this.translations.en[key];
        }
        
        return null;
    }
    
    /**
     * Register an event listener
     * @param {string} event - Event name (currently only 'languageChanged')
     * @param {Function} callback - Callback function to execute
     */
    on(event, callback) {
        if (event === 'languageChanged' && typeof callback === 'function') {
            this.listeners.languageChanged.push(callback);
        }
    }
    
    /**
     * Emit an event to all registered listeners
     * @param {string} event - Event name
     * @param {*} data - Data to pass to listeners
     */
    emit(event, data) {
        if (event === 'languageChanged') {
            this.listeners.languageChanged.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error('Error in languageChanged listener:', error);
                }
            });
        }
    }
    
    /**
     * Update translations object (useful for dynamic translation loading)
     * @param {Object} translations - New translations object
     */
    setTranslations(translations) {
        this.translations = translations;
        this.updateUI();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LanguageSwitcher;
}
