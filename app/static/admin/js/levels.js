/**
 * Levels Page Logic
 * 
 * Manages the dedicated levels page with CRUD operations, search, filtering, and multi-language support.
 * 
 * Features:
 * - List levels with EnhancedTable
 * - Search with 300ms debouncing
 * - Filter by subject
 * - Create/Edit levels with multi-language forms
 * - Delete levels with confirmation
 * - Breadcrumb navigation showing Subject → Levels
 * - Language switching
 * - Loading states and notifications
 * 
 * Requirements: 9.2, 9.5-9.6, 17.3, 2.1-2.6, 3.1-3.5, 11.1-11.8
 */

class LevelsPage {
    constructor() {
        this.levels = [];
        this.subjects = [];
        this.currentLevel = null;
        this.currentSubjectId = null;
        this.searchDebounceTimer = null;
        this.searchTerm = '';
        this.selectedSubjectFilter = '';
        
        // Pagination state
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalLevels = 0;
        
        // Initialize components
        this.table = null;
        this.multiLangForm = null;
        this.notification = new Notification();
        this.loadingSpinner = new LoadingSpinner();
        
        // Initialize page
        this.init();
    }
    
    /**
     * Initialize the page
     */
    async init() {
        try {
            // Check authentication
            await this.checkAuth();
            
            // Get subject_id from URL parameters
            this.parseUrlParameters();
            
            // Initialize table
            this.initTable();
            
            // Attach event listeners
            this.attachEventListeners();
            
            // Load subjects for dropdown and breadcrumb
            await this.loadSubjects();
            
            // Load levels only if a subject is selected
            if (this.currentSubjectId || this.selectedSubjectFilter) {
                await this.loadLevels();
            } else {
                // Show empty state with message to select a subject
                this.showEmptyState();
            }
            
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError('Failed to initialize page');
        }
    }
    
    /**
     * Parse URL parameters
     */
    parseUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        this.currentSubjectId = urlParams.get('subject_id');
        
        // If subject_id is provided, set it as the filter
        if (this.currentSubjectId) {
            this.selectedSubjectFilter = this.currentSubjectId;
        }
    }
    
    /**
     * Check if user is authenticated
     */
    async checkAuth() {
        try {
            const response = await fetch('/api/auth/me', {
                credentials: 'include'
            });
            
            if (!response.ok) {
                window.location.href = '/admin/login.html';
                return;
            }
            
            const data = await response.json();
            
            // Update user email display
            const emailElement = document.getElementById('current-user-email');
            if (emailElement) {
                emailElement.textContent = data.email || 'Admin';
            }
            
        } catch (error) {
            console.error('Auth check error:', error);
            window.location.href = '/admin/login.html';
        }
    }
    
    /**
     * Initialize enhanced table
     */
    initTable() {
        const columns = [
            {
                key: 'id',
                label: 'ID',
                sortable: true
            },
            {
                key: 'name',
                label: 'Name',
                sortable: true,
                render: (value, row) => {
                    // Display name in current language (default to English)
                    const lang = 'en';
                    return row[`name_${lang}`] || row.name_en || row.name || '-';
                }
            },
            {
                key: 'subject_id',
                label: 'Subject',
                sortable: false,
                render: (value, row) => {
                    // Look up subject name from the subjects list
                    if (!value) return '-';
                    const subject = this.subjects.find(s => s.id === value);
                    if (!subject) return '-';
                    const lang = 'en';
                    return subject[`name_${lang}`] || subject.name_en || subject.name || '-';
                }
            },
            {
                key: 'created_at',
                label: 'Created',
                sortable: true,
                render: (value) => {
                    if (!value) return '-';
                    const date = new Date(value);
                    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                }
            }
        ];
        
        this.table = new EnhancedTable('table-container', columns, {
            selectable: false, // CRITICAL: No bulk selection as per instructions
            actions: true,
            emptyMessage: 'No levels found',
            idField: 'id'
        });
        
        // Listen for table events
        this.table.on('rowEdit', (data) => {
            this.openEditModal(data.row);
        });
        
        this.table.on('rowDelete', (data) => {
            this.confirmDelete(data.row);
        });
    }
    
    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Search input with debouncing
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
        
        // Subject filter
        const subjectFilter = document.getElementById('subject-filter');
        if (subjectFilter) {
            subjectFilter.addEventListener('change', (e) => {
                this.selectedSubjectFilter = e.target.value;
                this.currentPage = 0; // Reset to first page on filter change
                if (this.selectedSubjectFilter) {
                    this.loadLevels();
                } else {
                    // No subject selected, show empty state
                    this.showEmptyState();
                }
            });
        }
        
        // Create level button
        const createBtn = document.getElementById('create-level-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.openCreateModal();
            });
        }
        
        // Modal close buttons
        const closeModalBtn = document.getElementById('close-modal-btn');
        const cancelBtn = document.getElementById('cancel-btn');
        
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => {
                this.closeModal();
            });
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeModal();
            });
        }
        
        // Form submission
        const form = document.getElementById('level-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }
        
        // Pagination controls
        const nextPageBtn = document.getElementById('test-next-page-btn');
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => {
                this.nextPage();
            });
        }
        
        const prevPageBtn = document.getElementById('test-prev-page-btn');
        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => {
                this.previousPage();
            });
        }
        
        const pageSizeSelect = document.getElementById('page-size');
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', (e) => {
                this.setPageSize(parseInt(e.target.value));
            });
        }
        
        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.handleLogout();
            });
        }
    }
    
    /**
     * Handle search with 300ms debouncing
     * Requirement 18.4: Debounce search after 300ms of inactivity
     */
    handleSearch(searchTerm) {
        // Clear existing timer
        if (this.searchDebounceTimer) {
            clearTimeout(this.searchDebounceTimer);
        }
        
        // Set new timer for 300ms
        this.searchDebounceTimer = setTimeout(() => {
            this.searchTerm = searchTerm.trim();
            this.currentPage = 0; // Reset to first page on search
            this.loadLevels();
        }, 300);
    }
    
    /**
     * Load subjects for dropdown and breadcrumb
     */
    async loadSubjects() {
        try {
            const params = new URLSearchParams({
                skip: '0',
                limit: '100' // Load subjects for dropdown
            });
            
            // Fetch subjects
            const response = await fetch(`/api/admin/subjects?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load subjects');
            }
            
            const data = await response.json();
            this.subjects = data.items || [];
            
            // Populate subject filter dropdown
            this.populateSubjectFilter();
            
            // Update breadcrumb if subject_id is provided
            if (this.currentSubjectId) {
                this.updateBreadcrumb();
            }
            
        } catch (error) {
            console.error('Error loading subjects:', error);
            this.notification.error('Failed to load subjects');
        }
    }
    
    /**
     * Populate subject filter dropdown
     */
    populateSubjectFilter() {
        const subjectFilter = document.getElementById('subject-filter');
        const subjectSelect = document.getElementById('subject-select');
        
        if (!subjectFilter || !this.subjects) return;
        
        const lang = 'en';
        
        // Clear all existing options
        while (subjectFilter.options.length > 0) {
            subjectFilter.remove(0);
        }
        
        // Add placeholder option
        const placeholderOption = document.createElement('option');
        placeholderOption.value = '';
        placeholderOption.textContent = 'Select a subject';
        subjectFilter.appendChild(placeholderOption);
        
        // Add subject options
        this.subjects.forEach(subject => {
            const option = document.createElement('option');
            option.value = subject.id;
            option.textContent = subject[`name_${lang}`] || subject.name_en || subject.name || `Subject ${subject.id}`;
            subjectFilter.appendChild(option);
        });
        
        // Set selected value if filter is active
        if (this.selectedSubjectFilter) {
            subjectFilter.value = this.selectedSubjectFilter;
        }
        
        // Also populate subject select in modal if it exists
        if (subjectSelect) {
            // Clear existing options (except placeholder)
            while (subjectSelect.options.length > 1) {
                subjectSelect.remove(1);
            }
            
            // Add subject options
            this.subjects.forEach(subject => {
                const option = document.createElement('option');
                option.value = subject.id;
                option.textContent = subject[`name_${lang}`] || subject.name_en || subject.name || `Subject ${subject.id}`;
                subjectSelect.appendChild(option);
            });
        }
    }
    
    /**
     * Update breadcrumb with subject name
     */
    updateBreadcrumb() {
        const breadcrumbSubjectName = document.getElementById('breadcrumb-subject-name');
        if (!breadcrumbSubjectName) return;
        
        // Find the subject
        const subject = this.subjects.find(s => s.id == this.currentSubjectId);
        
        if (subject) {
            const lang = 'en';
            breadcrumbSubjectName.textContent = subject[`name_${lang}`] || subject.name_en || subject.name || 'Unknown Subject';
        } else {
            breadcrumbSubjectName.textContent = 'Unknown Subject';
        }
    }
    
    /**
     * Load levels from API
     */
    async loadLevels() {
        try {
            // Show loading state
            this.showLoading();
            
            // Determine subject_id from selectedSubjectFilter or currentSubjectId
            const subjectId = this.selectedSubjectFilter || this.currentSubjectId;
            
            // If no subject is selected, show empty state
            if (!subjectId) {
                this.hideLoading();
                this.showEmptyState();
                return;
            }
            
            // Build query parameters
            const params = new URLSearchParams({
                skip: this.currentPage * this.pageSize,
                limit: this.pageSize
            });
            
            if (this.searchTerm) {
                params.append('search', this.searchTerm);
            }
            
            // Get current language for response (default to English)
            const lang = 'en';
            params.append('language', lang);
            
            // Fetch levels - subject_id must be in the path
            const response = await fetch(`/api/admin/subjects/${subjectId}/levels?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load levels');
            }
            
            const data = await response.json();
            this.levels = data.items || [];
            this.totalLevels = data.total || 0;
            
            // Update table
            this.table.setData(this.levels);
            
            // Update pagination display
            this.updatePaginationDisplay();
            
            // Hide loading, show table
            this.hideLoading();
            
            if (this.levels.length === 0) {
                this.showEmptyState();
            } else {
                this.showTable();
            }
            
        } catch (error) {
            console.error('Error loading levels:', error);
            this.hideLoading();
            this.showError('Failed to load levels');
        }
    }
    
    /**
     * Open create modal
     */
    openCreateModal() {
        this.currentLevel = null;
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.setAttribute('data-i18n', 'levels.createTitle');
            modalTitle.textContent = 'Create Level';
        }
        
        // Initialize multi-language form
        this.multiLangForm = new MultiLangForm('multilang-form-container', {
            fieldName: 'name',
            fieldType: 'input',
            label: 'Level Name',
            maxLength: 100,
            required: true
        });
        
        // Clear form
        this.multiLangForm.clear();
        
        // Populate subject dropdown
        this.populateSubjectFilter();
        
        // Pre-select subject if coming from subject page
        const subjectSelect = document.getElementById('subject-select');
        if (subjectSelect && this.currentSubjectId) {
            subjectSelect.value = this.currentSubjectId;
        }
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Open edit modal
     */
    openEditModal(level) {
        this.currentLevel = level;
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.setAttribute('data-i18n', 'levels.editTitle');
            modalTitle.textContent = 'Edit Level';
        }
        
        // Initialize multi-language form
        this.multiLangForm = new MultiLangForm('multilang-form-container', {
            fieldName: 'name',
            fieldType: 'input',
            label: 'Level Name',
            maxLength: 100,
            required: true
        });
        
        // Populate form with level data
        this.multiLangForm.setData({
            name_en: level.name_en || '',
            name_uz: level.name_uz || '',
            name_ru: level.name_ru || ''
        });
        
        // Populate subject dropdown
        this.populateSubjectFilter();
        
        // Set subject selection
        const subjectSelect = document.getElementById('subject-select');
        if (subjectSelect && level.subject_id) {
            subjectSelect.value = level.subject_id;
        }
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Show modal
     */
    showModal() {
        const modal = document.getElementById('level-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('level-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // Clear form
        if (this.multiLangForm) {
            this.multiLangForm.clear();
        }
        
        // Clear subject selection
        const subjectSelect = document.getElementById('subject-select');
        if (subjectSelect) {
            subjectSelect.value = '';
        }
        
        // Clear error
        const subjectError = document.getElementById('subject-error');
        if (subjectError) {
            subjectError.classList.add('hidden');
            subjectError.textContent = '';
        }
        
        this.currentLevel = null;
    }
    
    /**
     * Handle form submission
     */
    async handleSubmit() {
        try {
            // Validate multi-language form
            const validation = this.multiLangForm.validate();
            if (!validation.valid) {
                return;
            }
            
            // Validate subject selection
            const subjectSelect = document.getElementById('subject-select');
            const subjectError = document.getElementById('subject-error');
            
            if (!subjectSelect.value) {
                if (subjectError) {
                    subjectError.textContent = 'Please select a subject';
                    subjectError.classList.remove('hidden');
                }
                return;
            } else {
                if (subjectError) {
                    subjectError.classList.add('hidden');
                    subjectError.textContent = '';
                }
            }
            
            // Get form data
            const formData = this.multiLangForm.getData();
            formData.subject_id = parseInt(subjectSelect.value);
            
            // Disable form during submission
            this.multiLangForm.disable();
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
            }
            
            // Determine if creating or updating
            const isEdit = this.currentLevel !== null;
            const subjectId = parseInt(subjectSelect.value);
            const url = isEdit 
                ? `/api/admin/subjects/${subjectId}/levels/${this.currentLevel.id}`
                : `/api/admin/subjects/${subjectId}/levels`;
            const method = isEdit ? 'PUT' : 'POST';
            
            // Submit to API
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save level');
            }
            
            // Success
            this.notification.success(
                isEdit ? 'Level updated successfully' : 'Level created successfully'
            );
            
            // Close modal
            this.closeModal();
            
            // Reload levels
            await this.loadLevels();
            
        } catch (error) {
            console.error('Error saving level:', error);
            this.notification.error(error.message || 'Failed to save level');
            
        } finally {
            // Re-enable form
            if (this.multiLangForm) {
                this.multiLangForm.enable();
            }
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save';
            }
        }
    }
    
    /**
     * Confirm delete level
     */
    confirmDelete(level) {
        const lang = 'en';
        const levelName = level[`name_${lang}`] || level.name_en || level.name || 'this level';
        
        const dialog = new ConfirmationDialog({
            title: 'Delete Level',
            message: `Are you sure you want to delete "${levelName}"?`,
            confirmText: 'Delete',
            cancelText: 'Cancel',
            type: 'delete',
            cascadeWarning: 'This will also delete all tests and questions associated with this level.'
        });
        
        dialog.on('confirm', async () => {
            await this.deleteLevel(level);
        });
        
        dialog.show();
    }
    
    /**
     * Delete level
     */
    async deleteLevel(level) {
        try {
            // Get levelId and subject_id from the level object
            const levelId = level.id;
            const subjectId = level.subject_id;
            
            if (!subjectId) {
                throw new Error('Subject ID not found');
            }
            
            const response = await fetch(`/api/admin/subjects/${subjectId}/levels/${levelId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete level');
            }
            
            // Success
            this.notification.success('Level deleted successfully');
            
            // Reload levels
            await this.loadLevels();
            
        } catch (error) {
            console.error('Error deleting level:', error);
            this.notification.error('Failed to delete level');
        }
    }
    
    /**
     * Handle logout
     */
    async handleLogout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            window.location.href = '/admin/login.html';
            
        } catch (error) {
            console.error('Logout error:', error);
            window.location.href = '/admin/login.html';
        }
    }
    
    /**
     * Show loading state
     */
    showLoading() {
        const loadingState = document.getElementById('loading-state');
        const tableContainer = document.getElementById('table-container');
        const emptyState = document.getElementById('empty-state');
        const errorState = document.getElementById('error-state');
        
        if (loadingState) loadingState.classList.remove('hidden');
        if (tableContainer) tableContainer.classList.add('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        if (errorState) errorState.classList.add('hidden');
    }
    
    /**
     * Hide loading state
     */
    hideLoading() {
        const loadingState = document.getElementById('loading-state');
        if (loadingState) loadingState.classList.add('hidden');
    }
    
    /**
     * Show table
     */
    showTable() {
        const tableContainer = document.getElementById('table-container');
        const emptyState = document.getElementById('empty-state');
        const paginationContainer = document.getElementById('pagination-container');
        
        if (tableContainer) tableContainer.classList.remove('hidden');
        if (emptyState) emptyState.classList.add('hidden');
        if (paginationContainer) paginationContainer.classList.remove('hidden');
    }
    
    /**
     * Show empty state
     */
    showEmptyState() {
        const tableContainer = document.getElementById('table-container');
        const emptyState = document.getElementById('empty-state');
        const emptyStateMessage = document.getElementById('empty-state-message');
        const paginationContainer = document.getElementById('pagination-container');
        
        // Set appropriate message based on whether a subject is selected
        const subjectId = this.selectedSubjectFilter || this.currentSubjectId;
        if (emptyStateMessage) {
            if (subjectId) {
                emptyStateMessage.textContent = 'No levels found';
            } else {
                emptyStateMessage.textContent = 'Select a subject to view levels';
            }
        }
        
        if (tableContainer) tableContainer.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
        if (paginationContainer) paginationContainer.classList.add('hidden');
    }
    
    /**
     * Show error message
     */
    showError(message) {
        const errorState = document.getElementById('error-state');
        const errorMessage = document.getElementById('error-message');
        
        if (errorState && errorMessage) {
            errorMessage.textContent = message;
            errorState.classList.remove('hidden');
        }
        
        this.notification.error(message);
    }
    
    /**
     * Navigate to next page
     */
    nextPage() {
        const maxPage = Math.ceil(this.totalLevels / this.pageSize) - 1;
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.loadLevels();
        }
    }
    
    /**
     * Navigate to previous page
     */
    previousPage() {
        if (this.currentPage > 0) {
            this.currentPage--;
            this.loadLevels();
        }
    }
    
    /**
     * Set page size and reset to first page
     */
    setPageSize(size) {
        this.pageSize = size;
        this.currentPage = 0;
        this.loadLevels();
    }
    
    /**
     * Update pagination display
     */
    updatePaginationDisplay() {
        // Calculate pagination info
        const pageStart = this.currentPage * this.pageSize + 1;
        const pageEnd = Math.min((this.currentPage + 1) * this.pageSize, this.totalLevels);
        const maxPage = Math.ceil(this.totalLevels / this.pageSize);
        
        // Update page info display
        const pageInfoElement = document.getElementById('page-info');
        if (pageInfoElement) {
            if (this.totalLevels === 0) {
                pageInfoElement.textContent = 'No items';
            } else {
                pageInfoElement.textContent = `Showing ${pageStart}-${pageEnd} of ${this.totalLevels}`;
            }
        }
        
        // Update total count display
        const totalCountElement = document.getElementById('total-count');
        if (totalCountElement) {
            totalCountElement.textContent = this.totalLevels;
        }
        
        // Enable/disable next button
        const nextBtn = document.getElementById('test-next-page-btn');
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= maxPage - 1 || this.totalLevels === 0;
        }
        
        // Enable/disable previous button
        const prevBtn = document.getElementById('test-prev-page-btn');
        if (prevBtn) {
            prevBtn.disabled = this.currentPage === 0;
        }
        
        // Update current page display
        const currentPageElement = document.getElementById('current-page');
        if (currentPageElement) {
            currentPageElement.textContent = this.currentPage + 1;
        }
    }
}

// Initialize page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new LevelsPage();
    });
} else {
    new LevelsPage();
}
