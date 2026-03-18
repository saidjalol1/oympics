/**
 * Storage Utility
 * 
 * Provides a localStorage wrapper with error handling and convenience methods.
 * 
 * Features:
 * - localStorage wrapper with error handling
 * - Store/retrieve language preference
 * - Store/retrieve filter state
 * - Handle localStorage quota errors
 * - JSON serialization/deserialization
 * 
 * Requirements: 2.3, 2.4, 17.9
 */

const Storage = {
    /**
     * Storage keys
     */
    KEYS: {
        LANGUAGE: 'preferred_language',
        AUTH_TOKEN: 'auth_token',
        FILTER_STATE: 'filter_state',
        USER_PREFERENCES: 'user_preferences'
    },
    
    /**
     * Check if localStorage is available
     * @returns {boolean} True if localStorage is available
     */
    isAvailable() {
        try {
            const test = '__storage_test__';
            localStorage.setItem(test, test);
            localStorage.removeItem(test);
            return true;
        } catch (error) {
            console.warn('localStorage is not available:', error);
            return false;
        }
    },
    
    /**
     * Get item from localStorage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} Stored value or default value
     */
    get(key, defaultValue = null) {
        if (!this.isAvailable()) {
            return defaultValue;
        }
        
        try {
            const value = localStorage.getItem(key);
            return value !== null ? value : defaultValue;
        } catch (error) {
            console.error(`Error reading from localStorage (key: ${key}):`, error);
            return defaultValue;
        }
    },
    
    /**
     * Get JSON item from localStorage
     * @param {string} key - Storage key
     * @param {*} defaultValue - Default value if key doesn't exist or parsing fails
     * @returns {*} Parsed JSON value or default value
     */
    getJSON(key, defaultValue = null) {
        if (!this.isAvailable()) {
            return defaultValue;
        }
        
        try {
            const value = localStorage.getItem(key);
            if (value === null) {
                return defaultValue;
            }
            
            return JSON.parse(value);
        } catch (error) {
            console.error(`Error parsing JSON from localStorage (key: ${key}):`, error);
            return defaultValue;
        }
    },
    
    /**
     * Set item in localStorage
     * @param {string} key - Storage key
     * @param {string} value - Value to store
     * @returns {boolean} Success status
     */
    set(key, value) {
        if (!this.isAvailable()) {
            return false;
        }
        
        try {
            localStorage.setItem(key, value);
            return true;
        } catch (error) {
            // Handle quota exceeded error
            if (error.name === 'QuotaExceededError' || error.name === 'NS_ERROR_DOM_QUOTA_REACHED') {
                console.error('localStorage quota exceeded. Attempting to clear old data...');
                this.clearOldData();
                
                // Try again after clearing
                try {
                    localStorage.setItem(key, value);
                    return true;
                } catch (retryError) {
                    console.error('Failed to store data even after clearing:', retryError);
                    return false;
                }
            }
            
            console.error(`Error writing to localStorage (key: ${key}):`, error);
            return false;
        }
    },
    
    /**
     * Set JSON item in localStorage
     * @param {string} key - Storage key
     * @param {*} value - Value to store (will be JSON stringified)
     * @returns {boolean} Success status
     */
    setJSON(key, value) {
        try {
            const jsonString = JSON.stringify(value);
            return this.set(key, jsonString);
        } catch (error) {
            console.error(`Error stringifying JSON for localStorage (key: ${key}):`, error);
            return false;
        }
    },
    
    /**
     * Remove item from localStorage
     * @param {string} key - Storage key
     * @returns {boolean} Success status
     */
    remove(key) {
        if (!this.isAvailable()) {
            return false;
        }
        
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error(`Error removing from localStorage (key: ${key}):`, error);
            return false;
        }
    },
    
    /**
     * Clear all items from localStorage
     * @returns {boolean} Success status
     */
    clear() {
        if (!this.isAvailable()) {
            return false;
        }
        
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    },
    
    /**
     * Clear old data to free up space
     * Removes filter states and non-essential data
     */
    clearOldData() {
        const essentialKeys = [this.KEYS.LANGUAGE, this.KEYS.AUTH_TOKEN];
        
        try {
            // Get all keys
            const keys = Object.keys(localStorage);
            
            // Remove non-essential keys
            keys.forEach(key => {
                if (!essentialKeys.includes(key)) {
                    localStorage.removeItem(key);
                }
            });
            
            console.log('Cleared old data from localStorage');
        } catch (error) {
            console.error('Error clearing old data:', error);
        }
    },
    
    /**
     * Get language preference
     * Requirement 2.3: Persist language preference in browser storage
     * Requirement 2.4: Display content in previously selected language
     * 
     * @returns {string} Language code (en, uz, ru) or 'en' as default
     */
    getLanguage() {
        return this.get(this.KEYS.LANGUAGE, 'en');
    },
    
    /**
     * Set language preference
     * @param {string} languageCode - Language code (en, uz, ru)
     * @returns {boolean} Success status
     */
    setLanguage(languageCode) {
        return this.set(this.KEYS.LANGUAGE, languageCode);
    },
    
    /**
     * Get authentication token
     * @returns {string|null} Auth token or null
     */
    getAuthToken() {
        return this.get(this.KEYS.AUTH_TOKEN);
    },
    
    /**
     * Set authentication token
     * @param {string} token - Auth token
     * @returns {boolean} Success status
     */
    setAuthToken(token) {
        return this.set(this.KEYS.AUTH_TOKEN, token);
    },
    
    /**
     * Remove authentication token
     * @returns {boolean} Success status
     */
    removeAuthToken() {
        return this.remove(this.KEYS.AUTH_TOKEN);
    },
    
    /**
     * Get filter state for a specific page
     * Requirement 17.9: Persist filter state when navigating away and returning
     * 
     * @param {string} pageKey - Page identifier (e.g., 'subjects', 'tests')
     * @returns {Object|null} Filter state object or null
     */
    getFilterState(pageKey) {
        const allFilters = this.getJSON(this.KEYS.FILTER_STATE, {});
        return allFilters[pageKey] || null;
    },
    
    /**
     * Set filter state for a specific page
     * @param {string} pageKey - Page identifier (e.g., 'subjects', 'tests')
     * @param {Object} filterState - Filter state object
     * @returns {boolean} Success status
     */
    setFilterState(pageKey, filterState) {
        const allFilters = this.getJSON(this.KEYS.FILTER_STATE, {});
        allFilters[pageKey] = filterState;
        return this.setJSON(this.KEYS.FILTER_STATE, allFilters);
    },
    
    /**
     * Clear filter state for a specific page
     * @param {string} pageKey - Page identifier
     * @returns {boolean} Success status
     */
    clearFilterState(pageKey) {
        const allFilters = this.getJSON(this.KEYS.FILTER_STATE, {});
        delete allFilters[pageKey];
        return this.setJSON(this.KEYS.FILTER_STATE, allFilters);
    },
    
    /**
     * Clear all filter states
     * @returns {boolean} Success status
     */
    clearAllFilterStates() {
        return this.remove(this.KEYS.FILTER_STATE);
    },
    
    /**
     * Get user preferences
     * @returns {Object} User preferences object
     */
    getUserPreferences() {
        return this.getJSON(this.KEYS.USER_PREFERENCES, {});
    },
    
    /**
     * Set user preferences
     * @param {Object} preferences - Preferences object
     * @returns {boolean} Success status
     */
    setUserPreferences(preferences) {
        return this.setJSON(this.KEYS.USER_PREFERENCES, preferences);
    },
    
    /**
     * Get a specific user preference
     * @param {string} key - Preference key
     * @param {*} defaultValue - Default value if key doesn't exist
     * @returns {*} Preference value or default value
     */
    getUserPreference(key, defaultValue = null) {
        const preferences = this.getUserPreferences();
        return preferences[key] !== undefined ? preferences[key] : defaultValue;
    },
    
    /**
     * Set a specific user preference
     * @param {string} key - Preference key
     * @param {*} value - Preference value
     * @returns {boolean} Success status
     */
    setUserPreference(key, value) {
        const preferences = this.getUserPreferences();
        preferences[key] = value;
        return this.setUserPreferences(preferences);
    },
    
    /**
     * Get storage usage information
     * @returns {Object} Object with used and available space estimates
     */
    getStorageInfo() {
        if (!this.isAvailable()) {
            return { used: 0, available: 0, percentage: 0 };
        }
        
        try {
            let used = 0;
            
            // Calculate used space
            for (let key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    used += localStorage[key].length + key.length;
                }
            }
            
            // Most browsers have a 5-10MB limit
            const available = 5 * 1024 * 1024; // Assume 5MB
            const percentage = (used / available) * 100;
            
            return {
                used,
                available,
                percentage: Math.round(percentage)
            };
        } catch (error) {
            console.error('Error calculating storage info:', error);
            return { used: 0, available: 0, percentage: 0 };
        }
    },
    
    /**
     * Check if storage is nearly full (>80%)
     * @returns {boolean} True if storage is nearly full
     */
    isStorageNearlyFull() {
        const info = this.getStorageInfo();
        return info.percentage > 80;
    },
    
    /**
     * Export all localStorage data
     * @returns {Object} All localStorage data as object
     */
    exportAll() {
        if (!this.isAvailable()) {
            return {};
        }
        
        const data = {};
        
        try {
            for (let key in localStorage) {
                if (localStorage.hasOwnProperty(key)) {
                    data[key] = localStorage[key];
                }
            }
        } catch (error) {
            console.error('Error exporting localStorage:', error);
        }
        
        return data;
    },
    
    /**
     * Import localStorage data
     * @param {Object} data - Data to import
     * @param {boolean} clearFirst - Whether to clear existing data first
     * @returns {boolean} Success status
     */
    importAll(data, clearFirst = false) {
        if (!this.isAvailable()) {
            return false;
        }
        
        try {
            if (clearFirst) {
                this.clear();
            }
            
            for (let key in data) {
                if (data.hasOwnProperty(key)) {
                    localStorage.setItem(key, data[key]);
                }
            }
            
            return true;
        } catch (error) {
            console.error('Error importing localStorage:', error);
            return false;
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Storage;
}
