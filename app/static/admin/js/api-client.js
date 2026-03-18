/**
 * API Client Utility
 * 
 * Provides a fetch wrapper with error handling, authentication, and multipart support.
 * 
 * Features:
 * - Automatic authentication header injection
 * - Centralized error handling
 * - Support for JSON and multipart/form-data
 * - Network error handling
 * 
 * Requirements: 26.1, 26.2, 26.3, 26.4, 26.7
 */

class ApiClient {
    /**
     * Initialize the API client
     * @param {string} baseUrl - Base URL for API requests (default: '/api/admin')
     */
    constructor(baseUrl = '/api/admin') {
        this.baseUrl = baseUrl;
    }
    
    /**
     * Get authentication token from localStorage
     * @returns {string|null} Authentication token or null
     */
    getAuthToken() {
        try {
            return localStorage.getItem('access_token');
        } catch (error) {
            console.error('Error retrieving auth token:', error);
            return null;
        }
    }
    
    /**
     * Build headers for API request
     * @param {Object} customHeaders - Additional headers to include
     * @param {boolean} isMultipart - Whether this is a multipart/form-data request
     * @returns {Object} Headers object
     */
    buildHeaders(customHeaders = {}, isMultipart = false) {
        const headers = { ...customHeaders };
        
        // Add authentication header if token exists
        const token = this.getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        // Add Content-Type for JSON requests (not for multipart)
        if (!isMultipart && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }
        
        return headers;
    }
    
    /**
     * Make a GET request
     * @param {string} endpoint - API endpoint (relative to baseUrl)
     * @param {Object} params - Query parameters
     * @returns {Promise<any>} Response data
     */
    async get(endpoint, params = {}) {
        const url = this.buildUrl(endpoint, params);
        const headers = this.buildHeaders();
        
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            return this.handleApiError(error);
        }
    }
    
    /**
     * Make a POST request
     * @param {string} endpoint - API endpoint (relative to baseUrl)
     * @param {Object|FormData} data - Request body (JSON object or FormData)
     * @returns {Promise<any>} Response data
     */
    async post(endpoint, data) {
        const isFormData = data instanceof FormData;
        const url = this.buildUrl(endpoint);
        const headers = this.buildHeaders({}, isFormData);
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers,
                body: isFormData ? data : JSON.stringify(data)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            return this.handleApiError(error);
        }
    }
    
    /**
     * Make a PUT request
     * @param {string} endpoint - API endpoint (relative to baseUrl)
     * @param {Object|FormData} data - Request body (JSON object or FormData)
     * @returns {Promise<any>} Response data
     */
    async put(endpoint, data) {
        const isFormData = data instanceof FormData;
        const url = this.buildUrl(endpoint);
        const headers = this.buildHeaders({}, isFormData);
        
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers,
                body: isFormData ? data : JSON.stringify(data)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            return this.handleApiError(error);
        }
    }
    
    /**
     * Make a PATCH request
     * @param {string} endpoint - API endpoint (relative to baseUrl)
     * @param {Object|FormData} data - Request body (JSON object or FormData)
     * @returns {Promise<any>} Response data
     */
    async patch(endpoint, data = {}) {
        const isFormData = data instanceof FormData;
        const url = this.buildUrl(endpoint);
        const headers = this.buildHeaders({}, isFormData);
        
        try {
            const response = await fetch(url, {
                method: 'PATCH',
                headers,
                body: isFormData ? data : JSON.stringify(data)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            return this.handleApiError(error);
        }
    }
    
    /**
     * Make a DELETE request
     * @param {string} endpoint - API endpoint (relative to baseUrl)
     * @returns {Promise<any>} Response data
     */
    async delete(endpoint) {
        const url = this.buildUrl(endpoint);
        const headers = this.buildHeaders();
        
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            return this.handleApiError(error);
        }
    }
    
    /**
     * Build full URL with query parameters
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {string} Full URL
     */
    buildUrl(endpoint, params = {}) {
        const url = new URL(`${this.baseUrl}${endpoint}`, window.location.origin);
        
        // Add query parameters
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined) {
                url.searchParams.append(key, params[key]);
            }
        });
        
        return url.toString();
    }
    
    /**
     * Handle API response
     * @param {Response} response - Fetch response object
     * @returns {Promise<any>} Parsed response data
     */
    async handleResponse(response) {
        // Handle 204 No Content
        if (response.status === 204) {
            return { success: true };
        }
        
        // Try to parse JSON response
        let data;
        try {
            data = await response.json();
        } catch (error) {
            // If JSON parsing fails, return text
            data = await response.text();
        }
        
        // Handle error responses
        if (!response.ok) {
            throw {
                status: response.status,
                statusText: response.statusText,
                data
            };
        }
        
        return data;
    }
    
    /**
     * Handle API errors
     * Requirement 26.1: Database operation errors
     * Requirement 26.2: File upload errors
     * Requirement 26.3: Validation errors
     * Requirement 26.4: Network errors
     * Requirement 26.7: Unexpected errors
     * 
     * @param {Error|Object} error - Error object
     * @throws {Object} Formatted error object
     */
    handleApiError(error) {
        // Network error (no response from server)
        if (error instanceof TypeError && error.message.includes('fetch')) {
            throw {
                type: 'network',
                message: 'Connection lost. Please check your internet connection.',
                originalError: error
            };
        }
        
        // API error with response
        if (error.status) {
            const errorMessage = this.extractErrorMessage(error);
            
            // Validation error (400)
            if (error.status === 400) {
                throw {
                    type: 'validation',
                    message: errorMessage || 'Invalid request. Please check your input.',
                    status: 400,
                    data: error.data
                };
            }
            
            // Authentication error (401)
            if (error.status === 401) {
                throw {
                    type: 'authentication',
                    message: 'Authentication required. Please log in.',
                    status: 401
                };
            }
            
            // Authorization error (403)
            if (error.status === 403) {
                throw {
                    type: 'authorization',
                    message: 'You do not have permission to perform this action.',
                    status: 403
                };
            }
            
            // Not found error (404)
            if (error.status === 404) {
                throw {
                    type: 'not_found',
                    message: errorMessage || 'Resource not found.',
                    status: 404
                };
            }
            
            // Conflict error (409)
            if (error.status === 409) {
                throw {
                    type: 'conflict',
                    message: errorMessage || 'Resource already exists.',
                    status: 409
                };
            }
            
            // Server error (500+)
            if (error.status >= 500) {
                throw {
                    type: 'server',
                    message: 'An unexpected error occurred on the server. Please try again later.',
                    status: error.status,
                    originalError: error
                };
            }
            
            // Other errors
            throw {
                type: 'unknown',
                message: errorMessage || `An error occurred (${error.status}).`,
                status: error.status,
                data: error.data
            };
        }
        
        // Unknown error
        throw {
            type: 'unknown',
            message: error.message || 'An unexpected error occurred.',
            originalError: error
        };
    }
    
    /**
     * Extract error message from API response
     * @param {Object} error - Error object with data
     * @returns {string} Error message
     */
    extractErrorMessage(error) {
        if (!error.data) return null;
        
        // Handle string response
        if (typeof error.data === 'string') {
            return error.data;
        }
        
        // Handle object response with detail field
        if (error.data.detail) {
            return error.data.detail;
        }
        
        // Handle object response with message field
        if (error.data.message) {
            return error.data.message;
        }
        
        // Handle validation errors with field-specific messages
        if (error.data.errors && Array.isArray(error.data.errors)) {
            return error.data.errors.map(e => e.message || e.msg).join(', ');
        }
        
        return null;
    }
    
    // User Management API Methods
    
    /**
     * Get users with pagination and filtering
     * @param {number} skip - Number of users to skip
     * @param {number} limit - Number of users to return
     * @param {string} search - Search query for email
     * @param {boolean|null} verified - Filter by verification status
     * @param {boolean|null} isAdmin - Filter by admin status
     * @returns {Promise<Object>} Users data with pagination info
     */
    async getUsers(skip = 0, limit = 25, search = '', verified = null, isAdmin = null) {
        const params = { skip, limit };
        
        if (search) params.search = search;
        if (verified !== null) params.verified_only = verified;
        if (isAdmin !== null) params.is_admin = isAdmin;
        
        return await this.get('/users', params);
    }
    
    /**
     * Create a new user
     * @param {string} email - User email
     * @param {string} password - User password
     * @param {boolean} isVerified - Whether user is verified
     * @param {boolean} isAdmin - Whether user is admin
     * @returns {Promise<Object>} Created user data
     */
    async createUser(email, password, isVerified = false, isAdmin = false) {
        return await this.post('/users', {
            email,
            password,
            is_verified: isVerified,
            is_admin: isAdmin
        });
    }
    
    /**
     * Update an existing user
     * @param {number} userId - User ID
     * @param {Object} updates - Fields to update
     * @returns {Promise<Object>} Updated user data
     */
    async updateUser(userId, updates) {
        return await this.put(`/users/${userId}`, updates);
    }
    
    /**
     * Delete a user
     * @param {number} userId - User ID
     * @returns {Promise<Object>} Success response
     */
    async deleteUser(userId) {
        return await this.delete(`/users/${userId}`);
    }
    
    /**
     * Toggle user verification status
     * @param {number} userId - User ID
     * @returns {Promise<Object>} Updated user data
     */
    async toggleVerification(userId) {
        return await this.patch(`/users/${userId}/verify`);
    }
    
    /**
     * Get audit logs with pagination
     * @param {number} skip - Number of logs to skip
     * @param {number} limit - Number of logs to return
     * @returns {Promise<Object>} Audit logs data with pagination info
     */
    async getAuditLogs(skip = 0, limit = 25) {
        return await this.get('/audit-logs', { skip, limit });
    }
}

// Create singleton instance
const apiClient = new ApiClient();

// Make ApiClient available globally for the admin panel
window.ApiClient = apiClient;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, apiClient };
}
