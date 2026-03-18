/**
 * ImageUpload Component
 * 
 * Manages image uploads for questions with drag-and-drop support.
 * Supports up to 2 images per question with validation and preview.
 * 
 * Features:
 * - Drag-and-drop file upload with visual feedback
 * - Traditional file input with browse button
 * - Image validation (size, format, dimensions)
 * - Image preview with filename and size display
 * - 2-image limit enforcement
 * - Upload progress indicator
 * - Remove image functionality
 * 
 * Requirements: 19.1, 19.2, 19.3, 19.5, 19.6, 19.7, 20.1, 20.2, 20.3, 20.4
 */

class ImageUpload {
    /**
     * Initialize the ImageUpload component
     * @param {string} containerId - ID of the container element for the image upload
     * @param {Object} options - Configuration options
     * @param {number} options.maxImages - Maximum number of images allowed (default: 2)
     * @param {number} options.maxFileSize - Maximum file size in bytes (default: 5MB)
     * @param {Array<string>} options.allowedFormats - Allowed MIME types
     * @param {number} options.minDimension - Minimum image dimension in pixels
     * @param {number} options.maxDimension - Maximum image dimension in pixels
     */
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.options = {
            maxImages: options.maxImages || 2,
            maxFileSize: options.maxFileSize || 5242880, // 5MB
            allowedFormats: options.allowedFormats || ['image/jpeg', 'image/png', 'image/webp'],
            minDimension: options.minDimension || 100,
            maxDimension: options.maxDimension || 4000
        };
        
        this.images = []; // Array of { file: File, preview: string, id: string }
        this.listeners = {
            imageAdded: [],
            imageRemoved: [],
            validationError: []
        };
        
        this.render();
        this.attachEventListeners();
    }
    
    /**
     * Render the image upload component
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID "${this.containerId}" not found`);
            return;
        }
        
        const html = `
            <div class="image-upload-component">
                <!-- Drop Zone -->
                <div 
                    id="image-drop-zone" 
                    class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center transition-colors duration-200 hover:border-blue-400 cursor-pointer"
                    role="button"
                    tabindex="0"
                    aria-label="Upload images by dragging and dropping or clicking to browse"
                >
                    <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                    </svg>
                    <div class="mt-4">
                        <p class="text-sm text-gray-600">
                            <span class="font-semibold text-blue-600 hover:text-blue-500">Click to upload</span>
                            or drag and drop
                        </p>
                        <p class="text-xs text-gray-500 mt-1">
                            JPEG, PNG, or WebP up to 5MB (max 2 images)
                        </p>
                    </div>
                </div>
                
                <!-- Hidden File Input -->
                <input 
                    type="file" 
                    id="image-file-input" 
                    class="hidden" 
                    accept="image/jpeg,image/png,image/webp"
                    multiple
                    aria-label="Select image files"
                />
                
                <!-- Image Previews Container -->
                <div id="image-previews" class="mt-4 space-y-3">
                    <!-- Previews will be inserted here -->
                </div>
                
                <!-- Warning Message -->
                <div id="image-warning" class="hidden mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p class="text-sm text-yellow-800"></p>
                </div>
                
                <!-- Error Message -->
                <div id="image-error" class="hidden mt-3 p-3 bg-red-50 border border-red-200 rounded-md">
                    <p class="text-sm text-red-800"></p>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    /**
     * Attach event listeners to the component elements
     */
    attachEventListeners() {
        const dropZone = document.getElementById('image-drop-zone');
        const fileInput = document.getElementById('image-file-input');
        
        if (!dropZone || !fileInput) return;
        
        // Click to browse
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Keyboard accessibility
        dropZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInput.click();
            }
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
            fileInput.value = ''; // Reset input
        });
        
        // Drag and drop events
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('border-blue-500', 'bg-blue-50');
            dropZone.classList.remove('border-gray-300');
        });
        
        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('border-blue-500', 'bg-blue-50');
            dropZone.classList.add('border-gray-300');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('border-blue-500', 'bg-blue-50');
            dropZone.classList.add('border-gray-300');
            
            const files = e.dataTransfer.files;
            this.handleFiles(files);
        });
    }
    
    /**
     * Handle file selection/drop
     * @param {FileList} files - Files to process
     */
    async handleFiles(files) {
        this.hideMessages();
        
        const filesArray = Array.from(files);
        const availableSlots = this.options.maxImages - this.images.length;
        
        // Requirement 19.5: Check available slots before upload
        if (availableSlots === 0) {
            this.showError(`Maximum of ${this.options.maxImages} images allowed`);
            return;
        }
        
        // Requirement 19.6: Accept first 2 files when multiple dropped
        let filesToProcess = filesArray;
        let warning = null;
        
        if (filesArray.length > availableSlots) {
            filesToProcess = filesArray.slice(0, availableSlots);
            warning = `Only ${availableSlots} image(s) can be added. ${filesArray.length - availableSlots} file(s) were ignored.`;
        }
        
        // Process each file
        for (const file of filesToProcess) {
            try {
                await this.addImage(file);
            } catch (error) {
                this.showError(error.message);
            }
        }
        
        // Show warning if files were ignored
        if (warning) {
            this.showWarning(warning);
        }
    }
    
    /**
     * Add an image to the upload queue
     * @param {File} file - Image file to add
     * @returns {Promise<void>}
     */
    async addImage(file) {
        // Validate image
        const validation = await this.validateImage(file);
        if (!validation.valid) {
            throw new Error(validation.error);
        }
        
        // Generate preview
        const preview = await this.generatePreview(file);
        const id = this.generateId();
        
        // Add to images array
        this.images.push({
            file,
            preview,
            id,
            dimensions: validation.dimensions
        });
        
        // Render preview
        this.renderPreviews();
        
        // Emit event
        this.emit('imageAdded', { file, id });
    }
    
    /**
     * Remove an image from the upload queue
     * @param {string} id - Image ID to remove
     */
    removeImage(id) {
        const index = this.images.findIndex(img => img.id === id);
        if (index === -1) return;
        
        const image = this.images[index];
        
        // Revoke object URL to free memory
        URL.revokeObjectURL(image.preview);
        
        // Remove from array
        this.images.splice(index, 1);
        
        // Re-render previews
        this.renderPreviews();
        
        // Hide messages if no images
        if (this.images.length === 0) {
            this.hideMessages();
        }
        
        // Emit event
        this.emit('imageRemoved', { id });
    }
    
    /**
     * Validate an image file
     * @param {File} file - File to validate
     * @returns {Promise<Object>} Validation result with valid flag and error message
     */
    async validateImage(file) {
        // Requirement 19.2: Validate file format
        if (!this.options.allowedFormats.includes(file.type)) {
            return {
                valid: false,
                error: `Unsupported format. Allowed: JPEG, PNG, WebP`
            };
        }
        
        // Requirement 19.2: Validate file size
        if (file.size > this.options.maxFileSize) {
            const maxSizeMB = (this.options.maxFileSize / 1024 / 1024).toFixed(1);
            return {
                valid: false,
                error: `File size exceeds ${maxSizeMB}MB limit`
            };
        }
        
        if (file.size === 0) {
            return {
                valid: false,
                error: 'File is empty'
            };
        }
        
        // Requirement 19.3: Validate image dimensions
        try {
            const dimensions = await this.getImageDimensions(file);
            
            if (dimensions.width < this.options.minDimension || 
                dimensions.height < this.options.minDimension) {
                return {
                    valid: false,
                    error: `Image must be at least ${this.options.minDimension}x${this.options.minDimension} pixels`
                };
            }
            
            if (dimensions.width > this.options.maxDimension || 
                dimensions.height > this.options.maxDimension) {
                return {
                    valid: false,
                    error: `Image must not exceed ${this.options.maxDimension}x${this.options.maxDimension} pixels`
                };
            }
            
            return {
                valid: true,
                dimensions
            };
        } catch (error) {
            return {
                valid: false,
                error: 'Invalid image file'
            };
        }
    }
    
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
    }
    
    /**
     * Generate preview URL for an image file
     * @param {File} file - Image file
     * @returns {Promise<string>} Object URL for preview
     */
    generatePreview(file) {
        return Promise.resolve(URL.createObjectURL(file));
    }
    
    /**
     * Generate unique ID for an image
     * @returns {string} Unique ID
     */
    generateId() {
        return `img_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    /**
     * Render image previews
     */
    renderPreviews() {
        const container = document.getElementById('image-previews');
        if (!container) return;
        
        if (this.images.length === 0) {
            container.innerHTML = '';
            return;
        }
        
        const html = this.images.map((image, index) => `
            <div class="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                <!-- Preview Image -->
                <div class="flex-shrink-0">
                    <img 
                        src="${image.preview}" 
                        alt="Preview ${index + 1}"
                        class="h-16 w-16 object-cover rounded border border-gray-300"
                    />
                </div>
                
                <!-- File Info -->
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate" title="${image.file.name}">
                        ${image.file.name}
                    </p>
                    <p class="text-xs text-gray-500">
                        ${this.formatFileSize(image.file.size)} • ${image.dimensions.width}×${image.dimensions.height}px
                    </p>
                </div>
                
                <!-- Remove Button -->
                <button 
                    type="button"
                    class="flex-shrink-0 p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
                    onclick="window.imageUploadInstance.removeImage('${image.id}')"
                    aria-label="Remove image ${index + 1}"
                >
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    /**
     * Format file size in human-readable format
     * @param {number} bytes - File size in bytes
     * @returns {string} Formatted file size
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }
    
    /**
     * Show error message
     * @param {string} message - Error message to display
     */
    showError(message) {
        const errorDiv = document.getElementById('image-error');
        if (errorDiv) {
            errorDiv.querySelector('p').textContent = message;
            errorDiv.classList.remove('hidden');
        }
        
        this.emit('validationError', { message });
    }
    
    /**
     * Show warning message
     * @param {string} message - Warning message to display
     */
    showWarning(message) {
        const warningDiv = document.getElementById('image-warning');
        if (warningDiv) {
            warningDiv.querySelector('p').textContent = message;
            warningDiv.classList.remove('hidden');
        }
    }
    
    /**
     * Hide all messages
     */
    hideMessages() {
        const errorDiv = document.getElementById('image-error');
        const warningDiv = document.getElementById('image-warning');
        
        if (errorDiv) errorDiv.classList.add('hidden');
        if (warningDiv) warningDiv.classList.add('hidden');
    }
    
    /**
     * Get all images in the upload queue
     * @returns {Array<File>} Array of File objects
     */
    getImages() {
        return this.images.map(img => img.file);
    }
    
    /**
     * Get image data with metadata
     * @returns {Array<Object>} Array of image objects with file and metadata
     */
    getImageData() {
        return this.images.map(img => ({
            file: img.file,
            dimensions: img.dimensions,
            id: img.id
        }));
    }
    
    /**
     * Validate all images
     * @returns {Object} Validation result with valid flag and errors array
     */
    validate() {
        const errors = [];
        
        if (this.images.length > this.options.maxImages) {
            errors.push(`Maximum of ${this.options.maxImages} images allowed`);
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
    }
    
    /**
     * Clear all images
     */
    clear() {
        // Revoke all object URLs
        this.images.forEach(img => {
            URL.revokeObjectURL(img.preview);
        });
        
        this.images = [];
        this.renderPreviews();
        this.hideMessages();
    }
    
    /**
     * Register an event listener
     * @param {string} event - Event name (imageAdded, imageRemoved, validationError)
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
    module.exports = ImageUpload;
}
