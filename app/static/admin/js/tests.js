/**
 * Tests Page Logic
 * 
 * Manages the dedicated tests page with CRUD operations, search, filtering, and multi-language support.
 * 
 * Features:
 * - List tests with EnhancedTable
 * - Search with 300ms debouncing
 * - Filter by level, price range, date range
 * - Create/Edit tests with multi-language forms
 * - Delete tests with confirmation (cascade warning)
 * - Breadcrumb navigation showing Subject → Level → Tests
 * - Language switching
 * - Price display with "Free" for 0.00
 * - Loading states and notifications
 * 
 * Requirements: 9.3, 9.5, 9.6, 17.1, 17.4, 10.1, 15.1, 16.1, 8.5, 8.6, 8.7, 3.1, 8.1-8.4, 11.1
 */

class TestsPage {
    constructor() {
        this.tests = [];
        this.levels = [];
        this.subjects = [];
        this.currentTest = null;
        this.currentLevelId = null;
        this.currentSubjectId = null;
        this.searchDebounceTimer = null;
        this.searchTerm = '';
        this.selectedSubjectFilter = null;
        this.minPrice = null;
        this.maxPrice = null;
        this.startDateFrom = null;
        this.startDateTo = null;
        
        // Pagination state
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalTests = 0;
        
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
            
            // Get level_id and subject_id from URL parameters
            this.parseUrlParameters();
            
            // Initialize table
            this.initTable();
            
            // Attach event listeners
            this.attachEventListeners();
            
            // Load subjects for dropdowns and filters
            await this.loadSubjects();
            
            // Load tests
            await this.loadTests();
            
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
        this.currentLevelId = urlParams.get('level_id');
        this.currentSubjectId = urlParams.get('subject_id');
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
                    key: 'level',
                    label: 'Level',
                    sortable: false,
                    render: (value, row) => {
                        // Display level name in current language (default to English)
                        if (!row.level) return '-';
                        const lang = 'en';
                        return row.level[`name_${lang}`] || row.level.name_en || row.level.name || '-';
                    }
                },
                {
                    key: 'subject',
                    label: 'Subject',
                    sortable: false,
                    render: (value, row) => {
                        // Display subject name directly from test.level.subject
                        if (!row.level || !row.level.subject) return '-';
                        const lang = 'en';
                        return row.level.subject[`name_${lang}`] || row.level.subject.name_en || row.level.subject.name || '-';
                    }
                },
                {
                    key: 'price',
                    label: 'Price',
                    sortable: true,
                    render: (value) => {
                        // Display "Free" for 0.00, otherwise format with currency
                        if (value === 0 || value === '0.00' || value === 0.00) {
                            return '<span class="text-green-600 font-medium">Free</span>';
                        }
                        const price = typeof value === 'string' ? parseFloat(value) : value;
                        return `${price.toFixed(2)}`;
                    }
                },
                {
                    key: 'start_date',
                    label: 'Start Date',
                    sortable: true,
                    render: (value) => {
                        if (!value) return '-';
                        const date = new Date(value);
                        return date.toLocaleDateString();
                    }
                },
                {
                    key: 'end_date',
                    label: 'End Date',
                    sortable: true,
                    render: (value) => {
                        if (!value) return '-';
                        const date = new Date(value);
                        return date.toLocaleDateString();
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
                },
                {
                    key: 'actions',
                    label: 'Actions',
                    sortable: false,
                    render: (value, row) => {
                        return `
                            <div class="flex space-x-2">
                                <button class="view-btn text-green-600 hover:text-green-800 text-sm font-medium" data-id="${row.id}">
                                    View Questions
                                </button>
                                <button class="edit-btn text-blue-600 hover:text-blue-800 text-sm font-medium" data-id="${row.id}">
                                    Edit
                                </button>
                                <button class="delete-btn text-red-600 hover:text-red-800 text-sm font-medium" data-id="${row.id}">
                                    Delete
                                </button>
                            </div>
                        `;
                    }
                }
            ];

            this.table = new EnhancedTable('table-container', columns, {
                selectable: false, // CRITICAL: No bulk selection as per instructions
                actions: false, // We're handling actions manually in the Actions column
                emptyMessage: 'No tests found',
                idField: 'id',
                clickableRows: true // Enable clickable rows for navigation
            });

            const tableContainer = document.getElementById('table-container');
            if (tableContainer) {
                // Listen for table render event to attach row click handlers
                this.table.on('render', () => {
                    const tableRows = tableContainer.querySelectorAll('tbody tr');
                    tableRows.forEach(row => {
                        row.style.cursor = 'pointer';
                        row.addEventListener('click', (e) => {
                            // Don't navigate if clicking on buttons or action elements
                            if (e.target.closest('[data-action]') || 
                                e.target.closest('button') ||
                                e.target.closest('input')) {
                                return;
                            }

                            const rowId = row.getAttribute('data-row-id');
                            if (rowId) {
                                window.location.href = `/admin/questions?test_id=${rowId}`;
                            }
                        });
                    });
                });

                // Event delegation for action buttons to handle dynamically generated content
                tableContainer.addEventListener('click', (e) => {
                    if (e.target.classList.contains('view-btn')) {
                        e.stopPropagation(); // Prevent row click
                        const testId = e.target.getAttribute('data-id');
                        window.location.href = `/admin/questions?test_id=${testId}`;
                    }

                    if (e.target.classList.contains('edit-btn')) {
                        e.stopPropagation(); // Prevent row click
                        const testId = e.target.getAttribute('data-id');
                        const test = this.tests.find(t => t.id == testId);
                        if (test) {
                            this.openEditModal(test);
                        }
                    }

                    // Event delegation for delete buttons
                    if (e.target.classList.contains('delete-btn')) {
                        e.stopPropagation(); // Prevent row click
                        const testId = e.target.getAttribute('data-id');
                        const test = this.tests.find(t => t.id == testId);
                        if (test) {
                            this.confirmDelete(test);
                        }
                    }
                });
            }
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
                this.selectedSubjectFilter = e.target.value || null;
                this.currentPage = 0; // Reset to first page on filter change
                this.loadTests();
            });
        }
        
        // Price range filters
        const minPriceInput = document.getElementById('min-price');
        const maxPriceInput = document.getElementById('max-price');
        
        if (minPriceInput) {
            minPriceInput.addEventListener('change', (e) => {
                this.minPrice = e.target.value ? parseFloat(e.target.value) : null;
                this.currentPage = 0; // Reset to first page on filter change
                this.loadTests();
            });
        }
        
        if (maxPriceInput) {
            maxPriceInput.addEventListener('change', (e) => {
                this.maxPrice = e.target.value ? parseFloat(e.target.value) : null;
                this.currentPage = 0; // Reset to first page on filter change
                this.loadTests();
            });
        }
        
        // Date range filters
        const startDateFrom = document.getElementById('start-date-from');
        const startDateTo = document.getElementById('start-date-to');
        
        if (startDateFrom) {
            startDateFrom.addEventListener('change', (e) => {
                this.startDateFrom = e.target.value || null;
                this.currentPage = 0; // Reset to first page on filter change
                this.loadTests();
            });
        }
        
        if (startDateTo) {
            startDateTo.addEventListener('change', (e) => {
                this.startDateTo = e.target.value || null;
                this.currentPage = 0; // Reset to first page on filter change
                this.loadTests();
            });
        }
        
        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
        
        // Create test button
        const createBtn = document.getElementById('create-test-btn');
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
        const form = document.getElementById('test-form');
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
            this.loadTests();
        }, 300);
    }
    
    /**
     * Clear all filters
     */
    clearFilters() {
        // Clear search
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.value = '';
        this.searchTerm = '';
        
        // Clear subject filter
        const subjectFilter = document.getElementById('subject-filter');
        if (subjectFilter) subjectFilter.value = '';
        this.selectedSubjectFilter = null;
        
        // Clear price range
        const minPriceInput = document.getElementById('min-price');
        const maxPriceInput = document.getElementById('max-price');
        if (minPriceInput) minPriceInput.value = '';
        if (maxPriceInput) maxPriceInput.value = '';
        this.minPrice = null;
        this.maxPrice = null;
        
        // Clear date range
        const startDateFrom = document.getElementById('start-date-from');
        const startDateTo = document.getElementById('start-date-to');
        if (startDateFrom) startDateFrom.value = '';
        if (startDateTo) startDateTo.value = '';
        this.startDateFrom = null;
        this.startDateTo = null;
        
        // Reload tests
        this.loadTests();
    }
    
    /**
     * Load subjects for dropdown and breadcrumb
     */
    async loadSubjects() {
        try {
            const params = new URLSearchParams({
                skip: '0',
                limit: '100'
            });
            
            const response = await fetch(`/api/admin/subjects?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load subjects');
            }
            
            const data = await response.json();
            this.subjects = data.items || [];
            
            // Populate subject dropdown in modal
            this.populateSubjectDropdown();
            
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
     * Populate subject dropdown in modal
     */
    populateSubjectDropdown() {
        const subjectSelect = document.getElementById('subject-select');
        
        if (!subjectSelect || !this.subjects) return;
        
        const lang = 'en';
        
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

    /**
     * Populate subject filter dropdown
     */
    populateSubjectFilter() {
        const subjectFilter = document.getElementById('subject-filter');
        
        if (!subjectFilter || !this.subjects) return;
        
        const lang = 'en';
        
        // Clear existing options (except "All Subjects" placeholder)
        while (subjectFilter.options.length > 1) {
            subjectFilter.remove(1);
        }
        
        // Add subject options
        this.subjects.forEach(subject => {
            const option = document.createElement('option');
            option.value = subject.id;
            option.textContent = subject[`name_${lang}`] || subject.name_en || subject.name || `Subject ${subject.id}`;
            subjectFilter.appendChild(option);
        });
    }

    /**
     * Load levels for a specific subject
     */
    async loadLevelsForSubject(subjectId) {
        try {
            if (!subjectId) {
                this.levels = [];
                this.populateLevelDropdownInModal();
                return;
            }
            
            const params = new URLSearchParams({
                skip: '0',
                limit: '100'
            });
            
            const response = await fetch(`/api/admin/subjects/${subjectId}/levels?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load levels');
            }
            
            const data = await response.json();
            this.levels = data.items || [];
            
            // Populate level dropdown in modal
            this.populateLevelDropdownInModal();
            
        } catch (error) {
            console.error('Error loading levels for subject:', error);
            this.notification.error('Failed to load levels');
        }
    }

    /**
     * Populate level dropdown in modal only
     */
    populateLevelDropdownInModal() {
        const levelSelect = document.getElementById('level-select');
        
        if (!levelSelect) return;
        
        const lang = 'en';
        
        // Clear existing options (except placeholder)
        while (levelSelect.options.length > 1) {
            levelSelect.remove(1);
        }
        
        // Add level options
        if (this.levels && this.levels.length > 0) {
            this.levels.forEach(level => {
                const option = document.createElement('option');
                option.value = level.id;
                option.textContent = level[`name_${lang}`] || level.name_en || level.name || `Level ${level.id}`;
                levelSelect.appendChild(option);
            });
        }
    }
    
    /**
     * Build level-subject lookup map for efficient subject name display
     */
    /**
     * Update breadcrumb with subject and level names
     */
    updateBreadcrumb() {
        const breadcrumbSubjectName = document.getElementById('breadcrumb-subject-name');
        const breadcrumbSubjectLink = document.getElementById('breadcrumb-subject-link');
        const breadcrumbLevelName = document.getElementById('breadcrumb-level-name');
        const breadcrumbLevelLink = document.getElementById('breadcrumb-level-link');
        
        const lang = 'en';
        
        // Update subject breadcrumb
        if (this.currentSubjectId && breadcrumbSubjectName && breadcrumbSubjectLink) {
            const subject = this.subjects.find(s => s.id == this.currentSubjectId);
            if (subject) {
                breadcrumbSubjectName.textContent = subject[`name_${lang}`] || subject.name_en || subject.name || 'Unknown Subject';
                breadcrumbSubjectLink.href = `subjects.html`;
            }
        }
        
        // Update level breadcrumb
        if (this.currentLevelId && breadcrumbLevelName && breadcrumbLevelLink) {
            const level = this.levels.find(l => l.id == this.currentLevelId);
            if (level) {
                breadcrumbLevelName.textContent = level[`name_${lang}`] || level.name_en || level.name || 'Unknown Level';
                breadcrumbLevelLink.href = `levels.html?subject_id=${this.currentSubjectId || level.subject_id}`;
            }
        }
    }
    
    /**
     * Load tests from API
     */
    async loadTests() {
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
            
            if (this.selectedSubjectFilter) {
                params.append('subject_id', this.selectedSubjectFilter);
            }
            
            if (this.minPrice !== null) {
                params.append('min_price', this.minPrice.toString());
            }
            
            if (this.maxPrice !== null) {
                params.append('max_price', this.maxPrice.toString());
            }
            
            if (this.startDateFrom) {
                params.append('start_date_from', this.startDateFrom);
            }
            
            if (this.startDateTo) {
                params.append('start_date_to', this.startDateTo);
            }
            
            // Fetch tests
            const response = await fetch(`/api/admin/tests?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load tests');
            }
            
            const data = await response.json();
            this.tests = data.items || [];
            this.totalTests = data.total || 0;
            
            // Update table
            this.table.setData(this.tests);
            
            // Update pagination display
            this.updatePaginationDisplay();
            
            // Hide loading, show table
            this.hideLoading();
            
            if (this.tests.length === 0) {
                this.showEmptyState();
            } else {
                this.showTable();
            }
            
        } catch (error) {
            console.error('Error loading tests:', error);
            this.hideLoading();
            this.showError('Failed to load tests');
        }
    }
    
    /**
     * Open create modal
     */
    openCreateModal() {
        this.currentTest = null;
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Create Test';
        }
        
        // Initialize multi-language form
        this.multiLangForm = new MultiLangForm('multilang-form-container', {
            fieldName: 'name',
            fieldType: 'input',
            label: 'Test Name',
            maxLength: 100,
            required: true
        });
        
        // Clear form
        this.multiLangForm.clear();
        
        // Populate subject dropdown
        this.populateSubjectDropdown();
        
        // Clear level dropdown
        const levelSelect = document.getElementById('level-select');
        if (levelSelect) {
            while (levelSelect.options.length > 1) {
                levelSelect.remove(1);
            }
        }
        
        // Add subject change listener
        const subjectSelect = document.getElementById('subject-select');
        if (subjectSelect) {
            // Remove existing listeners
            const newSubjectSelect = subjectSelect.cloneNode(true);
            subjectSelect.parentNode.replaceChild(newSubjectSelect, subjectSelect);
            
            // Add new listener
            newSubjectSelect.addEventListener('change', async (e) => {
                const subjectId = e.target.value;
                if (subjectId) {
                    await this.loadLevelsForSubject(subjectId);
                } else {
                    // Clear level dropdown if no subject selected
                    const levelSelect = document.getElementById('level-select');
                    if (levelSelect) {
                        while (levelSelect.options.length > 1) {
                            levelSelect.remove(1);
                        }
                    }
                }
            });
        }
        
        // Clear price and dates
        const priceInput = document.getElementById('price-input');
        const startDateInput = document.getElementById('start-date-input');
        const endDateInput = document.getElementById('end-date-input');
        
        if (priceInput) priceInput.value = '0.00';
        if (startDateInput) startDateInput.value = '';
        if (endDateInput) endDateInput.value = '';
        
        // Clear errors
        this.clearFormErrors();
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Open edit modal
     */
    async openEditModal(test) {
        this.currentTest = test;
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.textContent = 'Edit Test';
        }
        
        // Initialize multi-language form
        this.multiLangForm = new MultiLangForm('multilang-form-container', {
            fieldName: 'name',
            fieldType: 'input',
            label: 'Test Name',
            maxLength: 100,
            required: true
        });
        
        // Populate form with test data
        this.multiLangForm.setData({
            name_en: test.name_en || '',
            name_uz: test.name_uz || '',
            name_ru: test.name_ru || ''
        });
        
        // Populate subject dropdown
        this.populateSubjectDropdown();
        
        // Find the subject for this test's level
        let testSubjectId = null;
        if (test.level && test.level.subject_id) {
            testSubjectId = test.level.subject_id;
        } else if (test.level_id) {
            // Fetch the level to get its subject_id
            try {
                const response = await fetch(`/api/admin/tests/${test.id}`, {
                    credentials: 'include'
                });
                if (response.ok) {
                    const testData = await response.json();
                    if (testData.level && testData.level.subject_id) {
                        testSubjectId = testData.level.subject_id;
                    }
                }
            } catch (error) {
                console.error('Error fetching test details:', error);
            }
        }
        
        // Set subject selection and load its levels
        const subjectSelect = document.getElementById('subject-select');
        if (subjectSelect && testSubjectId) {
            subjectSelect.value = testSubjectId;
            await this.loadLevelsForSubject(testSubjectId);
        }
        
        // Add subject change listener
        if (subjectSelect) {
            // Remove existing listeners
            const newSubjectSelect = subjectSelect.cloneNode(true);
            subjectSelect.parentNode.replaceChild(newSubjectSelect, subjectSelect);
            
            // Restore the selected value
            newSubjectSelect.value = testSubjectId || '';
            
            // Add new listener
            newSubjectSelect.addEventListener('change', async (e) => {
                const subjectId = e.target.value;
                if (subjectId) {
                    await this.loadLevelsForSubject(subjectId);
                } else {
                    // Clear level dropdown if no subject selected
                    const levelSelect = document.getElementById('level-select');
                    if (levelSelect) {
                        while (levelSelect.options.length > 1) {
                            levelSelect.remove(1);
                        }
                    }
                }
            });
        }
        
        // Set level selection
        const levelSelect = document.getElementById('level-select');
        if (levelSelect && test.level_id) {
            levelSelect.value = test.level_id;
        }
        
        // Set price
        const priceInput = document.getElementById('price-input');
        if (priceInput) {
            const price = typeof test.price === 'string' ? parseFloat(test.price) : test.price;
            priceInput.value = price.toFixed(2);
        }
        
        // Set dates
        const startDateInput = document.getElementById('start-date-input');
        const endDateInput = document.getElementById('end-date-input');
        
        if (startDateInput && test.start_date) {
            const startDate = new Date(test.start_date);
            startDateInput.value = startDate.toISOString().split('T')[0];
        }
        
        if (endDateInput && test.end_date) {
            const endDate = new Date(test.end_date);
            endDateInput.value = endDate.toISOString().split('T')[0];
        }
        
        // Clear errors
        this.clearFormErrors();
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Show modal
     */
    showModal() {
        const modal = document.getElementById('test-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('test-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // Clear form
        if (this.multiLangForm) {
            this.multiLangForm.clear();
        }
        
        // Clear selections
        const subjectSelect = document.getElementById('subject-select');
        const levelSelect = document.getElementById('level-select');
        
        if (subjectSelect) {
            subjectSelect.value = '';
        }
        
        if (levelSelect) {
            levelSelect.value = '';
        }
        
        // Clear errors
        this.clearFormErrors();
        
        this.currentTest = null;
    }
    
    /**
     * Clear form errors
     */
    clearFormErrors() {
        const subjectError = document.getElementById('subject-error');
        const levelError = document.getElementById('level-error');
        const priceError = document.getElementById('price-error');
        const dateError = document.getElementById('date-error');
        
        if (subjectError) {
            subjectError.classList.add('hidden');
            subjectError.textContent = '';
        }
        
        if (levelError) {
            levelError.classList.add('hidden');
            levelError.textContent = '';
        }
        
        if (priceError) {
            priceError.classList.add('hidden');
            priceError.textContent = '';
        }
        
        if (dateError) {
            dateError.classList.add('hidden');
            dateError.textContent = '';
        }
    }
    
    /**
     * Validate form
     */
    validateForm() {
        let isValid = true;
        
        // Validate multi-language form
        const mlValidation = this.multiLangForm.validate();
        if (!mlValidation.valid) {
            isValid = false;
        }
        
        // Validate subject selection
        const subjectSelect = document.getElementById('subject-select');
        const subjectError = document.getElementById('subject-error');
        
        if (!subjectSelect.value) {
            if (subjectError) {
                subjectError.textContent = 'Please select a subject';
                subjectError.classList.remove('hidden');
            }
            isValid = false;
        } else {
            if (subjectError) {
                subjectError.classList.add('hidden');
                subjectError.textContent = '';
            }
        }
        
        // Validate level selection
        const levelSelect = document.getElementById('level-select');
        const levelError = document.getElementById('level-error');
        
        if (!levelSelect.value) {
            if (levelError) {
                levelError.textContent = 'Please select a level';
                levelError.classList.remove('hidden');
            }
            isValid = false;
        } else {
            if (levelError) {
                levelError.classList.add('hidden');
                levelError.textContent = '';
            }
        }
        
        // Validate price
        const priceInput = document.getElementById('price-input');
        const priceError = document.getElementById('price-error');
        const price = parseFloat(priceInput.value);
        
        if (isNaN(price) || price < 0) {
            if (priceError) {
                priceError.textContent = 'Price must be 0 or greater';
                priceError.classList.remove('hidden');
            }
            isValid = false;
        } else {
            if (priceError) {
                priceError.classList.add('hidden');
                priceError.textContent = '';
            }
        }
        
        // Validate date range
        const startDateInput = document.getElementById('start-date-input');
        const endDateInput = document.getElementById('end-date-input');
        const dateError = document.getElementById('date-error');
        
        if (startDateInput.value && endDateInput.value) {
            const startDate = new Date(startDateInput.value);
            const endDate = new Date(endDateInput.value);
            
            if (endDate < startDate) {
                if (dateError) {
                    dateError.textContent = 'End date must be after start date';
                    dateError.classList.remove('hidden');
                }
                isValid = false;
            } else {
                if (dateError) {
                    dateError.classList.add('hidden');
                    dateError.textContent = '';
                }
            }
        } else {
            if (dateError) {
                dateError.classList.add('hidden');
                dateError.textContent = '';
            }
        }
        
        return isValid;
    }
    
    /**
     * Handle form submission
     */
    async handleSubmit() {
        try {
            // Validate form
            if (!this.validateForm()) {
                return;
            }
            
            // Get form data
            const formData = this.multiLangForm.getData();
            
            // Add level_id
            const levelSelect = document.getElementById('level-select');
            formData.level_id = parseInt(levelSelect.value);
            
            // Add price
            const priceInput = document.getElementById('price-input');
            formData.price = parseFloat(priceInput.value);
            
            // Add dates
            const startDateInput = document.getElementById('start-date-input');
            const endDateInput = document.getElementById('end-date-input');
            
            if (startDateInput.value) {
                formData.start_date = startDateInput.value + 'T00:00:00Z';
            }
            
            if (endDateInput.value) {
                formData.end_date = endDateInput.value + 'T23:59:59Z';
            }
            
            // Disable form during submission
            this.multiLangForm.disable();
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
            }
            
            // Determine if creating or updating
            const isEdit = this.currentTest !== null;
            const url = isEdit 
                ? `/api/admin/tests/${this.currentTest.id}`
                : '/api/admin/tests';
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
                throw new Error(error.detail || 'Failed to save test');
            }
            
            // Success
            this.notification.success(
                isEdit ? 'Test updated successfully' : 'Test created successfully'
            );
            
            // Close modal
            this.closeModal();
            
            // Reload tests
            await this.loadTests();
            
        } catch (error) {
            console.error('Error saving test:', error);
            this.notification.error(error.message || 'Failed to save test');
            
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
     * Confirm delete test
     */
    confirmDelete(test) {
        const lang = 'en';
        const testName = test[`name_${lang}`] || test.name_en || test.name || 'this test';
        
        const dialog = new ConfirmationDialog({
            title: 'Delete Test',
            message: `Are you sure you want to delete "${testName}"?`,
            confirmText: 'Delete',
            cancelText: 'Cancel',
            type: 'delete',
            cascadeWarning: 'Warning: Deleting this test will also delete all questions associated with it. This action cannot be undone.'
        });
        
        dialog.on('confirm', async () => {
            await this.deleteTest(test.id);
        });
        
        dialog.show();
    }
    
    /**
     * Delete test
     */
    async deleteTest(testId) {
        try {
            const response = await fetch(`/api/admin/tests/${testId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete test');
            }
            
            // Success
            this.notification.success('Test deleted successfully');
            
            // Reload tests
            await this.loadTests();
            
        } catch (error) {
            console.error('Error deleting test:', error);
            this.notification.error('Failed to delete test');
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
        const maxPage = Math.ceil(this.totalTests / this.pageSize) - 1;
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.loadTests();
        }
    }
    
    /**
     * Navigate to previous page
     */
    previousPage() {
        if (this.currentPage > 0) {
            this.currentPage--;
            this.loadTests();
        }
    }
    
    /**
     * Set page size and reset to first page
     */
    setPageSize(size) {
        this.pageSize = size;
        this.currentPage = 0;
        this.loadTests();
    }
    
    /**
     * Update pagination display
     */
    updatePaginationDisplay() {
        // Calculate pagination info
        const pageStart = this.currentPage * this.pageSize + 1;
        const pageEnd = Math.min((this.currentPage + 1) * this.pageSize, this.totalTests);
        const maxPage = Math.ceil(this.totalTests / this.pageSize);
        
        // Update page info display
        const pageInfoElement = document.getElementById('page-info');
        if (pageInfoElement) {
            if (this.totalTests === 0) {
                pageInfoElement.textContent = 'No items';
            } else {
                pageInfoElement.textContent = `Showing ${pageStart}-${pageEnd} of ${this.totalTests}`;
            }
        }
        
        // Update total count display
        const totalCountElement = document.getElementById('total-count');
        if (totalCountElement) {
            totalCountElement.textContent = this.totalTests;
        }
        
        // Enable/disable next button
        const nextBtn = document.getElementById('test-next-page-btn');
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= maxPage - 1 || this.totalTests === 0;
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
        new TestsPage();
    });
} else {
    new TestsPage();
}
