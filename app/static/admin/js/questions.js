/**
 * Questions Page Logic
 * 
 * Manages the dedicated questions page with CRUD operations, search, filtering, image management, and multi-language support.
 * 
 * Features:
 * - List questions with EnhancedTable
 * - Search with 300ms debouncing across all languages
 * - Filter by correct answer and image presence
 * - Create/Edit questions with multi-language forms
 * - Manage question options (2-10 options, A-J)
 * - Upload and manage images (up to 2 per question)
 * - Display image thumbnails in table
 * - Full-size image modal on click
 * - Delete questions with confirmation
 * - Breadcrumb navigation showing Subject → Level → Test → Questions
 * - Language switching
 * - Loading states and notifications
 * 
 * Requirements: 9.4, 9.5, 9.6, 17.1, 17.5, 10.1, 15.1, 16.1, 7.1, 3.1, 4.1, 11.1
 */

class QuestionsPage {
    constructor() {
        this.questions = [];
        this.tests = [];
        this.levels = [];
        this.subjects = [];
        this.currentQuestion = null;
        this.currentTestId = null;
        this.currentLevelId = null;
        this.currentSubjectId = null;
        this.searchDebounceTimer = null;
        this.searchTerm = '';
        this.selectedAnswerFilter = '';
        this.hasImagesFilter = '';
        this.questionOptions = []; // Array of option objects
        this.nextOptionLabel = 'A'; // Next available option label
        
        // Pagination state
        this.currentPage = 0;
        this.pageSize = 10;
        this.totalQuestions = 0;
        
        // Initialize components
        this.table = null;
        this.questionTextForm = null;
        this.imageUpload = null;
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
            
            // Get test_id, level_id, and subject_id from URL parameters
            this.parseUrlParameters();
            
            // Initialize table
            this.initTable();
            
            // Attach event listeners
            this.attachEventListeners();
            
            // Load hierarchy data for breadcrumb
            await this.loadHierarchyData();
            
            // Load questions
            await this.loadQuestions();
            
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
        this.currentTestId = urlParams.get('test_id');
        this.currentLevelId = urlParams.get('level_id');
        this.currentSubjectId = urlParams.get('subject_id');
        
        if (!this.currentTestId) {
            this.showError('Test ID is required');
            throw new Error('Test ID is required');
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
                key: 'text',
                label: 'Question',
                sortable: true,
                render: (value, row) => {
                    // Display question text in current language (truncated, default to English)
                    const lang = 'en';
                    const text = row[`text_${lang}`] || row.text_en || row.text || '-';
                    const maxLength = 100;
                    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
                }
            },
            {
                key: 'correct_answer',
                label: 'Answer',
                sortable: true,
                render: (value) => {
                    return `<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">${value || '-'}</span>`;
                }
            },
            {
                key: 'images',
                label: 'Images',
                sortable: false,
                render: (value, row) => {
                    // Display image thumbnails
                    if (!row.images || row.images.length === 0) {
                        return '<span class="text-gray-400 text-xs">No images</span>';
                    }
                    
                    const firstImage = row.images[0];
                    const thumbnail = `<img src="${firstImage.image_path}" alt="Thumbnail" class="h-8 w-8 object-cover rounded border border-gray-300 cursor-pointer hover:opacity-75" onclick="window.questionsPageInstance.viewImage('${firstImage.image_path}')">`;
                    
                    return `<div class="flex space-x-1">${thumbnail}</div>`;
                }
            },
            {
                key: 'created_at',
                label: 'Created',
                sortable: true,
                render: (value) => {
                    if (!value) return '-';
                    const date = new Date(value);
                    return date.toLocaleDateString();
                }
            }
        ];
        
        this.table = new EnhancedTable('table-container', columns, {
            selectable: false, // CRITICAL: No bulk selection as per instructions
            actions: true,
            emptyMessage: 'No questions found',
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
        
        // Correct answer filter
        const answerFilter = document.getElementById('correct-answer-filter');
        if (answerFilter) {
            answerFilter.addEventListener('change', (e) => {
                this.selectedAnswerFilter = e.target.value;
                this.currentPage = 0; // Reset to first page on filter change
                this.loadQuestions();
            });
        }
        
        // Has images filter
        const imagesFilter = document.getElementById('has-images-filter');
        if (imagesFilter) {
            imagesFilter.addEventListener('change', (e) => {
                this.hasImagesFilter = e.target.value;
                this.currentPage = 0; // Reset to first page on filter change
                this.loadQuestions();
            });
        }
        
        // Create question button
        const createBtn = document.getElementById('create-question-btn');
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
        const form = document.getElementById('question-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }
        
        // Add option button
        const addOptionBtn = document.getElementById('add-option-btn');
        if (addOptionBtn) {
            addOptionBtn.addEventListener('click', () => {
                this.addOption();
            });
        }
        
        // Image view modal close
        const closeImageModalBtn = document.getElementById('close-image-modal-btn');
        if (closeImageModalBtn) {
            closeImageModalBtn.addEventListener('click', () => {
                this.closeImageModal();
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
            this.loadQuestions();
        }, 300);
    }
    
    /**
     * Load hierarchy data (subjects, levels, tests) for breadcrumb
     */
    async loadHierarchyData() {
        try {
            const lang = 'en';
            
            // Load test data
            if (this.currentTestId) {
                const testResponse = await fetch(`/api/admin/tests/${this.currentTestId}?language=${lang}`, {
                    credentials: 'include'
                });
                
                if (testResponse.ok) {
                    const test = await testResponse.json();
                    this.currentLevelId = test.level_id;
                    
                    // Update breadcrumb
                    const breadcrumbTestName = document.getElementById('breadcrumb-test-name');
                    const breadcrumbTestLink = document.getElementById('breadcrumb-test-link');
                    if (breadcrumbTestName && test) {
                        breadcrumbTestName.textContent = test[`name_${lang}`] || test.name_en || test.name || 'Test';
                    }
                    if (breadcrumbTestLink) {
                        breadcrumbTestLink.href = `tests.html?level_id=${this.currentLevelId}&subject_id=${this.currentSubjectId}`;
                    }
                }
            }
            
            // Load level data
            if (this.currentLevelId) {
                const levelResponse = await fetch(`/api/admin/levels/${this.currentLevelId}?language=${lang}`, {
                    credentials: 'include'
                });
                
                if (levelResponse.ok) {
                    const level = await levelResponse.json();
                    this.currentSubjectId = level.subject_id;
                    
                    // Update breadcrumb
                    const breadcrumbLevelName = document.getElementById('breadcrumb-level-name');
                    const breadcrumbLevelLink = document.getElementById('breadcrumb-level-link');
                    if (breadcrumbLevelName && level) {
                        breadcrumbLevelName.textContent = level[`name_${lang}`] || level.name_en || level.name || 'Level';
                    }
                    if (breadcrumbLevelLink) {
                        breadcrumbLevelLink.href = `levels.html?subject_id=${this.currentSubjectId}`;
                    }
                }
            }
            
            // Load subject data
            if (this.currentSubjectId) {
                const subjectResponse = await fetch(`/api/admin/subjects/${this.currentSubjectId}?language=${lang}`, {
                    credentials: 'include'
                });
                
                if (subjectResponse.ok) {
                    const subject = await subjectResponse.json();
                    
                    // Update breadcrumb
                    const breadcrumbSubjectName = document.getElementById('breadcrumb-subject-name');
                    const breadcrumbSubjectLink = document.getElementById('breadcrumb-subject-link');
                    if (breadcrumbSubjectName && subject) {
                        breadcrumbSubjectName.textContent = subject[`name_${lang}`] || subject.name_en || subject.name || 'Subject';
                    }
                    if (breadcrumbSubjectLink) {
                        breadcrumbSubjectLink.href = 'subjects.html';
                    }
                }
            }
            
        } catch (error) {
            console.error('Error loading hierarchy data:', error);
        }
    }
    
    /**
     * Load questions from API
     */
    async loadQuestions() {
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
            
            if (this.selectedAnswerFilter) {
                params.append('correct_answer', this.selectedAnswerFilter);
            }
            
            if (this.hasImagesFilter) {
                params.append('has_images', this.hasImagesFilter);
            }
            
            // Get current language for response (default to English)
            const lang = 'en';
            params.append('language', lang);
            
            // Fetch questions for the current test
            const response = await fetch(`/api/admin/tests/${this.currentTestId}/questions?${params.toString()}`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load questions');
            }
            
            const data = await response.json();
            this.questions = data.items || [];
            this.totalQuestions = data.total || 0;
            
            // Update table
            this.table.setData(this.questions);
            
            // Update pagination display
            this.updatePaginationDisplay();
            
            // Hide loading, show table
            this.hideLoading();
            
            if (this.questions.length === 0) {
                this.showEmptyState();
            } else {
                this.showTable();
            }
            
        } catch (error) {
            console.error('Error loading questions:', error);
            this.hideLoading();
            this.showError('Failed to load questions');
        }
    }
    
    /**
     * Open create modal
     */
    openCreateModal() {
        this.currentQuestion = null;
        this.questionOptions = [];
        this.nextOptionLabel = 'A';
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.setAttribute('data-i18n', 'questions.createTitle');
            modalTitle.textContent = 'Create Question';
        }
        
        // Initialize question text multi-language form
        this.questionTextForm = new MultiLangForm('question-text-container', {
            fieldName: 'text',
            fieldType: 'textarea',
            label: 'Question Text',
            maxLength: 1000,
            required: true,
            rows: 4
        });
        
        // Clear form
        this.questionTextForm.clear();
        
        // Clear correct answer
        const correctAnswerSelect = document.getElementById('correct-answer-select');
        if (correctAnswerSelect) {
            correctAnswerSelect.value = '';
        }
        
        // Initialize image upload component
        this.imageUpload = new ImageUpload('image-upload-container', {
            maxImages: 2,
            maxFileSize: 5242880, // 5MB
            allowedFormats: ['image/jpeg', 'image/png', 'image/webp'],
            minDimension: 100,
            maxDimension: 4000
        });
        
        // Store instance globally for onclick handlers
        window.imageUploadInstance = this.imageUpload;
        
        // Initialize with 3 default options (A, B, and C)
        this.addOption();
        this.addOption();
        this.addOption();
        
        // Clear errors
        this.clearFormErrors();
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Open edit modal
     */
    async openEditModal(question) {
        this.currentQuestion = question;
        this.questionOptions = [];
        this.nextOptionLabel = 'A';
        
        // Update modal title
        const modalTitle = document.getElementById('modal-title');
        if (modalTitle) {
            modalTitle.setAttribute('data-i18n', 'questions.editTitle');
            modalTitle.textContent = 'Edit Question';
        }
        
        // Initialize question text multi-language form
        this.questionTextForm = new MultiLangForm('question-text-container', {
            fieldName: 'text',
            fieldType: 'textarea',
            label: 'Question Text',
            maxLength: 1000,
            required: true,
            rows: 4
        });
        
        // Populate form with question data
        this.questionTextForm.setData({
            text_en: question.text_en || '',
            text_uz: question.text_uz || '',
            text_ru: question.text_ru || ''
        });
        
        // Populate existing options
        if (question.options && question.options.length > 0) {
            // Clear default options
            this.questionOptions = [];
            
            // Add existing options
            question.options.forEach(opt => {
                this.questionOptions.push({
                    label: opt.label,
                    form: null
                });
            });
            
            // Render options
            this.renderOptions();
            
            // Populate option data
            question.options.forEach(opt => {
                const form = this.questionOptions.find(o => o.label === opt.label)?.form;
                if (form) {
                    const fieldName = `option_${opt.label}_text`;
                    form.setData({
                        [`${fieldName}_en`]: opt.text_en || '',
                        [`${fieldName}_uz`]: opt.text_uz || '',
                        [`${fieldName}_ru`]: opt.text_ru || ''
                    });
                }
            });
        }
        
        // Set correct answer
        const correctAnswerSelect = document.getElementById('correct-answer-select');
        if (correctAnswerSelect && question.correct_answer) {
            correctAnswerSelect.value = question.correct_answer;
        }
        
        // Initialize image upload component
        this.imageUpload = new ImageUpload('image-upload-container', {
            maxImages: 2,
            maxFileSize: 5242880, // 5MB
            allowedFormats: ['image/jpeg', 'image/png', 'image/webp'],
            minDimension: 100,
            maxDimension: 4000
        });
        
        // Store instance globally for onclick handlers
        window.imageUploadInstance = this.imageUpload;
        
        // Clear errors
        this.clearFormErrors();
        
        // Show modal
        this.showModal();
    }
    
    /**
     * Load question options for editing
     */
    async loadQuestionOptions(questionId) {
        try {
            const response = await fetch(`/api/admin/questions/${questionId}/options`, {
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to load question options');
            }
            
            const data = await response.json();
            const options = data.items || [];
            
            // Sort options by label
            options.sort((a, b) => a.label.localeCompare(b.label));
            
            // Add each option to the form
            for (const option of options) {
                this.addOption(option);
            }
            
            // Update next option label
            if (options.length > 0) {
                const lastLabel = options[options.length - 1].label;
                this.nextOptionLabel = String.fromCharCode(lastLabel.charCodeAt(0) + 1);
            }
            
        } catch (error) {
            console.error('Error loading question options:', error);
            this.notification.error('Failed to load question options');
        }
    }
    
    /**
     * Add a new option to the form
     */
    addOption(optionData = null) {
        // Check if we've reached the maximum (10 options: A-J)
        if (this.questionOptions.length >= 10) {
            this.notification.warning('Maximum of 10 options allowed (A-J)');
            return;
        }
        
        // Determine the label for this option
        const label = optionData ? optionData.label : this.nextOptionLabel;
        
        // Create option object
        const option = {
            id: optionData ? optionData.id : null,
            label: label,
            form: null
        };
        
        // Add to options array
        this.questionOptions.push(option);
        
        // Update next option label
        if (!optionData) {
            this.nextOptionLabel = String.fromCharCode(this.nextOptionLabel.charCodeAt(0) + 1);
        }
        
        // Render options
        this.renderOptions();
        
        // If option data is provided, populate the form
        if (optionData) {
            // Wait for form to be rendered, then set data
            setTimeout(() => {
                const currentOption = this.questionOptions.find(opt => opt.label === label);
                if (currentOption && currentOption.form) {
                    const fieldName = `option_${label}_text`;
                    currentOption.form.setData({
                        [`${fieldName}_en`]: optionData.text_en || '',
                        [`${fieldName}_uz`]: optionData.text_uz || '',
                        [`${fieldName}_ru`]: optionData.text_ru || ''
                    });
                }
            }, 100);
        }
        
        // Update add button state
        this.updateAddOptionButton();
    }
    
    /**
     * Remove an option from the form
     */
    removeOption(label) {
        // Find option index
        const index = this.questionOptions.findIndex(opt => opt.label === label);
        if (index === -1) return;
        
        // Check minimum options (must have at least 2)
        if (this.questionOptions.length <= 2) {
            this.notification.warning('Minimum of 2 options required');
            return;
        }
        
        // Remove from array
        this.questionOptions.splice(index, 1);
        
        // Re-render options
        this.renderOptions();
        
        // Update add button state
        this.updateAddOptionButton();
    }
    
    /**
     * Render all options
     */
    renderOptions() {
        const container = document.getElementById('options-container');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Render each option
        this.questionOptions.forEach((option, index) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'border border-gray-200 rounded-lg p-4';
            optionDiv.id = `option-${option.label}`;
            
            // Create header with label and remove button
            const header = document.createElement('div');
            header.className = 'flex items-center justify-between mb-3';
            header.innerHTML = `
                <h4 class="text-sm font-medium text-gray-700">Option ${option.label}</h4>
                <button
                    type="button"
                    class="text-red-600 hover:text-red-800 text-sm"
                    onclick="window.questionsPageInstance.removeOption('${option.label}')"
                >
                    Remove
                </button>
            `;
            optionDiv.appendChild(header);
            
            // Create container for multi-language form
            const formContainer = document.createElement('div');
            formContainer.id = `option-form-${option.label}`;
            optionDiv.appendChild(formContainer);
            
            container.appendChild(optionDiv);
            
            // Initialize multi-language form for this option
            option.form = new MultiLangForm(`option-form-${option.label}`, {
                fieldName: `option_${option.label}_text`,
                fieldType: 'input',
                label: `Option ${option.label} Text`,
                maxLength: 1000,
                required: true
            });
        });
    }
    
    /**
     * Update add option button state
     */
    updateAddOptionButton() {
        const addBtn = document.getElementById('add-option-btn');
        if (!addBtn) return;
        
        if (this.questionOptions.length >= 10) {
            addBtn.disabled = true;
            addBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            addBtn.disabled = false;
            addBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }
    
    /**
     * Show modal
     */
    showModal() {
        const modal = document.getElementById('question-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
        
        // Store instance globally for onclick handlers
        window.questionsPageInstance = this;
    }
    
    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('question-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // Clear forms
        if (this.questionTextForm) {
            this.questionTextForm.clear();
        }
        
        if (this.imageUpload) {
            this.imageUpload.clear();
        }
        
        // Clear options
        this.questionOptions = [];
        this.nextOptionLabel = 'A';
        const optionsContainer = document.getElementById('options-container');
        if (optionsContainer) {
            optionsContainer.innerHTML = '';
        }
        
        // Clear errors
        this.clearFormErrors();
        
        this.currentQuestion = null;
    }
    
    /**
     * Clear form errors
     */
    clearFormErrors() {
        const correctAnswerError = document.getElementById('correct-answer-error');
        
        if (correctAnswerError) {
            correctAnswerError.classList.add('hidden');
            correctAnswerError.textContent = '';
        }
    }
    
    /**
     * Handle form submission
     */
    async handleSubmit() {
        try {
            // Validate question text form
            const textValidation = this.questionTextForm.validate();
            if (!textValidation.valid) {
                return;
            }
            
            // Validate correct answer
            const correctAnswerSelect = document.getElementById('correct-answer-select');
            const correctAnswerError = document.getElementById('correct-answer-error');
            
            if (!correctAnswerSelect.value) {
                if (correctAnswerError) {
                    correctAnswerError.textContent = 'Please select the correct answer';
                    correctAnswerError.classList.remove('hidden');
                }
                return;
            } else {
                if (correctAnswerError) {
                    correctAnswerError.classList.add('hidden');
                    correctAnswerError.textContent = '';
                }
            }
            
            // Validate options (minimum 2, maximum 10)
            if (this.questionOptions.length < 2) {
                this.notification.error('Minimum of 2 options required');
                return;
            }
            
            if (this.questionOptions.length > 10) {
                this.notification.error('Maximum of 10 options allowed');
                return;
            }
            
            // Validate all option forms
            let allOptionsValid = true;
            for (const option of this.questionOptions) {
                const validation = option.form.validate();
                if (!validation.valid) {
                    allOptionsValid = false;
                }
            }
            
            if (!allOptionsValid) {
                this.notification.error('Please fill in all option fields');
                return;
            }
            
            // Validate that correct answer matches one of the options
            const correctAnswer = correctAnswerSelect.value;
            const hasMatchingOption = this.questionOptions.some(opt => opt.label === correctAnswer);
            
            if (!hasMatchingOption) {
                if (correctAnswerError) {
                    correctAnswerError.textContent = `Correct answer ${correctAnswer} must match one of the option labels`;
                    correctAnswerError.classList.remove('hidden');
                }
                return;
            }
            
            // Get form data
            const questionData = this.questionTextForm.getData();
            questionData.correct_answer = correctAnswer;
            
            // Disable form during submission
            this.questionTextForm.disable();
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Saving...';
            }
            
            // Determine if creating or updating
            const isEdit = this.currentQuestion !== null;
            
            // Create FormData for multipart upload (for images)
            const formData = new FormData();
            formData.append('text_en', questionData.text_en);
            formData.append('text_uz', questionData.text_uz);
            formData.append('text_ru', questionData.text_ru);
            formData.append('correct_answer', correctAnswer);
            
            // Add images if any
            const images = this.imageUpload.getImages();
            images.forEach((image, index) => {
                formData.append(`image${index + 1}`, image);
            });
            
            // Add options as JSON
            const optionsData = this.questionOptions.map(opt => {
                const optData = opt.form.getData();
                console.log(`Option ${opt.label} raw data:`, optData);
                const fieldName = `option_${opt.label}_text`;
                return {
                    label: opt.label,
                    text_en: optData[`${fieldName}_en`],
                    text_uz: optData[`${fieldName}_uz`],
                    text_ru: optData[`${fieldName}_ru`]
                };
            });
            console.log('Final options being sent:', optionsData);
            formData.append('options', JSON.stringify(optionsData));
            
            // Submit to API
            const url = isEdit 
                ? `/api/admin/tests/${this.currentTestId}/questions/${this.currentQuestion.id}`
                : `/api/admin/tests/${this.currentTestId}/questions`;
            const method = isEdit ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                credentials: 'include',
                body: formData
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save question');
            }
            
            // Success
            this.notification.success(
                isEdit ? 'Question updated successfully' : 'Question created successfully'
            );
            
            // Close modal
            this.closeModal();
            
            // Reload questions
            await this.loadQuestions();
            
        } catch (error) {
            console.error('Error saving question:', error);
            this.notification.error(error.message || 'Failed to save question');
            
        } finally {
            // Re-enable form
            if (this.questionTextForm) {
                this.questionTextForm.enable();
            }
            const submitBtn = document.getElementById('submit-btn');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Save';
            }
        }
    }
    
    /**
     * Confirm delete question
     */
    confirmDelete(question) {
        const lang = 'en';
        const questionText = question[`text_${lang}`] || question.text_en || question.text || 'this question';
        const truncatedText = questionText.length > 50 ? questionText.substring(0, 50) + '...' : questionText;
        
        const dialog = new ConfirmationDialog({
            title: 'Delete Question',
            message: `Are you sure you want to delete "${truncatedText}"?`,
            confirmText: 'Delete',
            cancelText: 'Cancel',
            type: 'delete',
            cascadeWarning: question.images && question.images.length > 0 
                ? 'This will also delete all images associated with this question.' 
                : null
        });
        
        dialog.on('confirm', async () => {
            await this.deleteQuestion(question.id);
        });
        
        dialog.show();
    }
    
    /**
     * Delete question
     */
    async deleteQuestion(questionId) {
        try {
            const response = await fetch(`/api/admin/tests/${this.currentTestId}/questions/${questionId}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete question');
            }
            
            // Success
            this.notification.success('Question deleted successfully');
            
            // Reload questions
            await this.loadQuestions();
            
        } catch (error) {
            console.error('Error deleting question:', error);
            this.notification.error('Failed to delete question');
        }
    }
    
    /**
     * View image in full-size modal
     */
    viewImage(imagePath) {
        const modal = document.getElementById('image-view-modal');
        const modalImage = document.getElementById('modal-image');
        
        if (modal && modalImage) {
            modalImage.src = imagePath;
            modal.classList.remove('hidden');
        }
    }
    
    /**
     * Close image view modal
     */
    closeImageModal() {
        const modal = document.getElementById('image-view-modal');
        if (modal) {
            modal.classList.add('hidden');
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
        const maxPage = Math.ceil(this.totalQuestions / this.pageSize) - 1;
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.loadQuestions();
        }
    }
    
    /**
     * Navigate to previous page
     */
    previousPage() {
        if (this.currentPage > 0) {
            this.currentPage--;
            this.loadQuestions();
        }
    }
    
    /**
     * Set page size and reset to first page
     */
    setPageSize(size) {
        this.pageSize = size;
        this.currentPage = 0;
        this.loadQuestions();
    }
    
    /**
     * Update pagination display
     */
    updatePaginationDisplay() {
        // Calculate pagination info
        const pageStart = this.currentPage * this.pageSize + 1;
        const pageEnd = Math.min((this.currentPage + 1) * this.pageSize, this.totalQuestions);
        const maxPage = Math.ceil(this.totalQuestions / this.pageSize);
        
        // Update page info display
        const pageInfoElement = document.getElementById('page-info');
        if (pageInfoElement) {
            if (this.totalQuestions === 0) {
                pageInfoElement.textContent = 'No items';
            } else {
                pageInfoElement.textContent = `Showing ${pageStart}-${pageEnd} of ${this.totalQuestions}`;
            }
        }
        
        // Update total count display
        const totalCountElement = document.getElementById('total-count');
        if (totalCountElement) {
            totalCountElement.textContent = this.totalQuestions;
        }
        
        // Enable/disable next button
        const nextBtn = document.getElementById('test-next-page-btn');
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= maxPage - 1 || this.totalQuestions === 0;
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
        new QuestionsPage();
    });
} else {
    new QuestionsPage();
}
