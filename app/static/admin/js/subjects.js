/**
 * Subjects Page Logic
 * 
 * Manages the dedicated subjects page with CRUD operations, search, and multi-language support.
 * 
 * Features:
 * - List subjects with EnhancedTable
 * - Search with 300ms debouncing
 * - Create/Edit subjects with multi-language forms
 * - Delete subjects with confirmation
 * - Language switching
 * - Loading states and notifications
 * 
 * Requirements: 9.1, 9.5, 17.1, 18.1, 18.4, 2.1-2.6, 3.1-3.5, 11.1-11.8
 */

// Import components (using script tags in HTML)
// Components are loaded globally from their respective files

class SubjectsPage {
    constructor() {
        this.subjects = [];
        this.currentSubject = null;
        this.searchDebounceTimer = null;
        this.searchTerm = '';
        
        // Pagination state
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalSubjects = 0;
        
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
            
            // Initialize table
            this.initTable();
            
            // Attach event listeners
            this.attachEventListeners();
            
            // Load subjects
            await this.loadSubjects();
            
        } catch (error) {
            console.error('Initialization error:', error);
            this.showError('Failed to initialize page');
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
            emptyMessage: 'No subjects found',
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
        
        // Create subject button
        const createBtn = document.getElementById('create-subject-btn');
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
        const form = document.getElementById('subject-form');
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
            this.loadSubjects();
        }, 300);
    }
    
    /**
     * Load subjects from API
     */
    async loadSubjects() {
        try {
            // Show loading state
            this.showLoading();
            
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
            
            // Fetch subjects
            const response = await fetch(`/api/admin/subjects?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load subjects');
            }
            
            const data = await response.json();
            this.subjects = data.subjects || data.items || [];
            this.totalSubjects = data.total || 0;
            
            // Update table
            this.table.setData(this.subjects);
            
            // Update pagination display
            this.updatePaginationDisplay();
            
            // Hide loading, show table
            this.hideLoading();
            
            if (this.subjects.length === 0) {
                this.showEmptyState();
            } else {
                this.showTable();
            }
            
        } catch (error) {
            console.error('Error loading subjects:', error);
            this.hideLoading();
            this.showError('Failed to load subjects');
        }
    }
    
    /**
     * Open create modal
     */
    openCreateModal() {
        this.currentSubject = null;
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.setAttribute('data-i18n', 'subjects.createTitle');
            modalTitle.textContent = 'Create Subject';
        }
        
        // Initialize multi-language form
        this.multiLangForm = new MultiLangForm('multilang-form-container', {
            fieldName: 'name',
            fieldType: 'input',
            label: 'Subject Name',
            maxLength: 100,
            required: true
        });
        
        // Clear form
        this.multiLangForm.clear();
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Open edit modal
     */
    openEditModal(subject) {
        this.currentSubject = subject;
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.setAttribute('data-i18n', 'subjects.editTitle');
            modalTitle.textContent = 'Edit Subject';
        }
        
        // Initialize multi-language form
        this.multiLangForm = new MultiLangForm('multilang-form-container', {
            fieldName: 'name',
            fieldType: 'input',
            label: 'Subject Name',
            maxLength: 100,
            required: true
        });
        
        // Populate form with subject data
        this.multiLangForm.setData({
            name_en: subject.name_en || '',
            name_uz: subject.name_uz || '',
            name_ru: subject.name_ru || ''
        });
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Show modal
     */
    showModal() {
        const modal = document.getElementById('subject-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('subject-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // Clear form
        if (this.multiLangForm) {
            this.multiLangForm.clear();
        }
        
        this.currentSubject = null;
    }
    
    /**
     * Handle form submission
     */
    async handleSubmit() {
        try {
            // Validate form
            const validation = this.multiLangForm.validate();
            if (!validation.valid) {
                return;
            }
            
            // Get form data
            const formData = this.multiLangForm.getData();
            
            // Disable form during submission
            this.multiLangForm.disable();
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
            }
            
            // Determine if creating or updating
            const isEdit = this.currentSubject !== null;
            const url = isEdit 
                ? `/api/admin/subjects/${this.currentSubject.id}`
                : '/api/admin/subjects';
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
                throw new Error(error.detail || 'Failed to save subject');
            }
            
            // Success
            this.notification.success(
                isEdit ? 'Subject updated successfully' : 'Subject created successfully'
            );
            
            // Close modal
            this.closeModal();
            
            // Reload subjects
            await this.loadSubjects();
            
        } catch (error) {
            console.error('Error saving subject:', error);
            this.notification.error(error.message || 'Failed to save subject');
            
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
     * Confirm delete subject
     */
    confirmDelete(subject) {
        const dialog = new ConfirmationDialog({
            title: 'Delete Subject',
            message: `Are you sure you want to delete "${subject.name_en || subject.name}"?`,
            confirmText: 'Delete',
            cancelText: 'Cancel',
            type: 'delete',
            cascadeWarning: 'This will also delete all levels, tests, and questions associated with this subject.'
        });
        
        dialog.on('confirm', async () => {
            await this.deleteSubject(subject.id);
        });
        
        dialog.show();
    }
    
    /**
     * Delete subject
     */
    async deleteSubject(subjectId) {
        try {
            const response = await fetch(`/api/admin/subjects/${subjectId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete subject');
            }
            
            // Success
            this.notification.success('Subject deleted successfully');
            
            // Reload subjects
            await this.loadSubjects();
            
        } catch (error) {
            console.error('Error deleting subject:', error);
            this.notification.error('Failed to delete subject');
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
        const paginationContainer = document.getElementById('pagination-container');
        
        if (tableContainer) tableContainer.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
        if (paginationContainer) paginationContainer.classList.add('hidden');
    }
    
    /**
     * Navigate to next page
     */
    nextPage() {
        const maxPage = Math.ceil(this.totalSubjects / this.pageSize) - 1;
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.loadSubjects();
        }
    }
    
    /**
     * Navigate to previous page
     */
    previousPage() {
        if (this.currentPage > 0) {
            this.currentPage--;
            this.loadSubjects();
        }
    }
    
    /**
     * Set page size and reset to first page
     */
    setPageSize(size) {
        this.pageSize = size;
        this.currentPage = 0;
        this.loadSubjects();
    }
    
    /**
     * Update pagination display
     */
    updatePaginationDisplay() {
        // Calculate pagination info
        const pageStart = this.currentPage * this.pageSize + 1;
        const pageEnd = Math.min((this.currentPage + 1) * this.pageSize, this.totalSubjects);
        const maxPage = Math.ceil(this.totalSubjects / this.pageSize);
        
        // Update page info display
        const pageInfoElement = document.getElementById('page-info');
        if (pageInfoElement) {
            if (this.totalSubjects === 0) {
                pageInfoElement.textContent = 'No items';
            } else {
                pageInfoElement.textContent = `Showing ${pageStart}-${pageEnd} of ${this.totalSubjects}`;
            }
        }
        
        // Update total count display
        const totalCountElement = document.getElementById('total-count');
        if (totalCountElement) {
            totalCountElement.textContent = this.totalSubjects;
        }
        
        // Enable/disable next button
        const nextBtn = document.getElementById('test-next-page-btn');
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= maxPage - 1 || this.totalSubjects === 0;
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
}

// Initialize page when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new SubjectsPage();
    });
} else {
    new SubjectsPage();
}
