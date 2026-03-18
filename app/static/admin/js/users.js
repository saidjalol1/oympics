/**
 * Users Page Management
 * Handles user CRUD operations for the dedicated users page
 */

class UsersPageManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 25;
        this.totalCount = 0;
        this.currentFilters = {};
        this.searchTimeout = null;
        this.users = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadUsers();
        
        // Load current user info
        this.loadCurrentUser();
    }

    setupEventListeners() {
        // Search input with debouncing
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.handleSearch(e.target.value);
                }, 300);
            });
        }

        // Filter dropdowns
        const verifiedFilter = document.getElementById('verified-filter');
        const adminFilter = document.getElementById('admin-filter');
        
        if (verifiedFilter) {
            verifiedFilter.addEventListener('change', (e) => {
                this.handleFilter('verified', e.target.value);
            });
        }
        
        if (adminFilter) {
            adminFilter.addEventListener('change', (e) => {
                this.handleFilter('admin', e.target.value);
            });
        }

        // Create user button
        const createUserBtn = document.querySelector('[data-action="create-user"]');
        if (createUserBtn) {
            createUserBtn.addEventListener('click', () => this.showCreateUserModal());
        }

        // Clear filters button
        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => this.clearFilters());
        }

        // Pagination controls
        const prevPageBtn = document.getElementById('prev-page-btn');
        const nextPageBtn = document.getElementById('next-page-btn');
        const pageSizeSelect = document.getElementById('page-size');

        if (prevPageBtn) {
            prevPageBtn.addEventListener('click', () => this.goToPreviousPage());
        }
        
        if (nextPageBtn) {
            nextPageBtn.addEventListener('click', () => this.goToNextPage());
        }
        
        if (pageSizeSelect) {
            pageSizeSelect.addEventListener('change', (e) => {
                this.pageSize = parseInt(e.target.value);
                this.currentPage = 1;
                this.loadUsers();
            });
        }

        // Modal event listeners
        this.setupModalEventListeners();

        // Logout button
        const logoutBtn = document.querySelector('[data-action="logout"]');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    setupModalEventListeners() {
        // Close modal buttons
        document.querySelectorAll('[data-action="close-modal"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modalId = e.target.getAttribute('data-modal');
                this.hideModal(modalId);
            });
        });

        // Create user form
        const createUserForm = document.getElementById('create-user-form');
        if (createUserForm) {
            createUserForm.addEventListener('submit', (e) => this.handleCreateUser(e));
        }

        // Edit user form
        const editUserForm = document.getElementById('edit-user-form');
        if (editUserForm) {
            editUserForm.addEventListener('submit', (e) => this.handleEditUser(e));
        }

        // Confirm delete button
        const confirmDeleteBtn = document.querySelector('[data-action="confirm-delete"]');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.confirmDeleteUser());
        }
    }

    async loadCurrentUser() {
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const user = await response.json();
                const emailElement = document.getElementById('current-user-email');
                if (emailElement) {
                    emailElement.textContent = user.email;
                }
            }
        } catch (error) {
            console.error('Error loading current user:', error);
        }
    }

    async loadUsers() {
        this.showLoading();
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                size: this.pageSize,
                ...this.currentFilters
            });

            const response = await fetch(`/api/admin/users?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.users = data.items || [];
            this.totalCount = data.total || 0;
            
            this.renderUsers();
            this.updatePagination();
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading users:', error);
            this.showError('Failed to load users. Please try again.');
            this.hideLoading();
        }
    }

    showLoading() {
        document.getElementById('loading-state').classList.remove('hidden');
        document.getElementById('table-container').classList.add('hidden');
        document.getElementById('empty-state').classList.add('hidden');
        document.getElementById('error-state').classList.add('hidden');
    }

    hideLoading() {
        document.getElementById('loading-state').classList.add('hidden');
    }

    showError(message) {
        const errorState = document.getElementById('error-state');
        const errorMessage = document.getElementById('error-message');
        
        if (errorMessage) {
            errorMessage.textContent = message;
        }
        
        if (errorState) {
            errorState.classList.remove('hidden');
        }
    }

    renderUsers() {
        const tbody = document.getElementById('users-table-body');
        const tableContainer = document.getElementById('table-container');
        const emptyState = document.getElementById('empty-state');

        if (!tbody) return;

        if (this.users.length === 0) {
            tableContainer.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }

        tableContainer.classList.remove('hidden');
        emptyState.classList.add('hidden');

        tbody.innerHTML = this.users.map(user => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${user.id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${user.email}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.is_verified 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                    }">
                        ${user.is_verified ? 'Verified' : 'Unverified'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.is_admin 
                            ? 'bg-blue-100 text-blue-800' 
                            : 'bg-gray-100 text-gray-800'
                    }">
                        ${user.is_admin ? 'Admin' : 'User'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${new Date(user.created_at).toLocaleDateString()}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button 
                        class="text-blue-600 hover:text-blue-900 transition-colors"
                        onclick="usersPageManager.showEditUserModal(${user.id})"
                    >
                        Edit
                    </button>
                    <button 
                        class="text-red-600 hover:text-red-900 transition-colors"
                        onclick="usersPageManager.showDeleteUserModal(${user.id})"
                    >
                        Delete
                    </button>
                </td>
            </tr>
        `).join('');
    }

    updatePagination() {
        const paginationContainer = document.getElementById('pagination-container');
        const pageStart = document.getElementById('page-start');
        const pageEnd = document.getElementById('page-end');
        const totalCount = document.getElementById('total-count');
        const prevPageBtn = document.getElementById('prev-page-btn');
        const nextPageBtn = document.getElementById('next-page-btn');

        if (this.users.length === 0) {
            paginationContainer.classList.add('hidden');
            return;
        }

        paginationContainer.classList.remove('hidden');

        const start = (this.currentPage - 1) * this.pageSize + 1;
        const end = Math.min(start + this.users.length - 1, this.totalCount);

        if (pageStart) pageStart.textContent = start;
        if (pageEnd) pageEnd.textContent = end;
        if (totalCount) totalCount.textContent = this.totalCount;

        if (prevPageBtn) {
            prevPageBtn.disabled = this.currentPage <= 1;
        }
        
        if (nextPageBtn) {
            nextPageBtn.disabled = end >= this.totalCount;
        }
    }

    handleSearch(query) {
        if (query.trim()) {
            this.currentFilters.search = query.trim();
        } else {
            delete this.currentFilters.search;
        }
        
        this.currentPage = 1;
        this.loadUsers();
        this.updateActiveFilters();
    }

    handleFilter(type, value) {
        if (value) {
            this.currentFilters[type] = value;
        } else {
            delete this.currentFilters[type];
        }
        
        this.currentPage = 1;
        this.loadUsers();
        this.updateActiveFilters();
    }

    updateActiveFilters() {
        const activeFilters = document.getElementById('active-filters');
        const filterBadges = document.getElementById('filter-badges');
        
        if (!activeFilters || !filterBadges) return;

        const hasFilters = Object.keys(this.currentFilters).length > 0;
        
        if (hasFilters) {
            activeFilters.classList.remove('hidden');
            
            const badges = Object.entries(this.currentFilters).map(([key, value]) => {
                let label = '';
                switch (key) {
                    case 'search':
                        label = `Search: "${value}"`;
                        break;
                    case 'verified':
                        label = `Verified: ${value === 'true' ? 'Yes' : 'No'}`;
                        break;
                    case 'admin':
                        label = `Admin: ${value === 'true' ? 'Yes' : 'No'}`;
                        break;
                }
                
                return `<span class="inline-flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    ${label}
                    <button class="ml-1 text-blue-600 hover:text-blue-800" onclick="usersPageManager.removeFilter('${key}')">×</button>
                </span>`;
            }).join('');
            
            filterBadges.innerHTML = badges;
        } else {
            activeFilters.classList.add('hidden');
        }
    }

    removeFilter(key) {
        delete this.currentFilters[key];
        
        // Update UI controls
        if (key === 'search') {
            const searchInput = document.getElementById('search-input');
            if (searchInput) searchInput.value = '';
        } else if (key === 'verified') {
            const verifiedFilter = document.getElementById('verified-filter');
            if (verifiedFilter) verifiedFilter.value = '';
        } else if (key === 'admin') {
            const adminFilter = document.getElementById('admin-filter');
            if (adminFilter) adminFilter.value = '';
        }
        
        this.currentPage = 1;
        this.loadUsers();
        this.updateActiveFilters();
    }

    clearFilters() {
        this.currentFilters = {};
        
        // Reset UI controls
        const searchInput = document.getElementById('search-input');
        const verifiedFilter = document.getElementById('verified-filter');
        const adminFilter = document.getElementById('admin-filter');
        
        if (searchInput) searchInput.value = '';
        if (verifiedFilter) verifiedFilter.value = '';
        if (adminFilter) adminFilter.value = '';
        
        this.currentPage = 1;
        this.loadUsers();
        this.updateActiveFilters();
    }

    goToPreviousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadUsers();
        }
    }

    goToNextPage() {
        const maxPage = Math.ceil(this.totalCount / this.pageSize);
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.loadUsers();
        }
    }

    showCreateUserModal() {
        const modal = document.getElementById('create-user-modal');
        if (modal) {
            modal.classList.remove('hidden');
            
            // Reset form
            const form = document.getElementById('create-user-form');
            if (form) {
                form.reset();
            }
        }
    }

    showEditUserModal(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        const modal = document.getElementById('edit-user-modal');
        if (!modal) return;

        // Populate form
        document.getElementById('edit-user-id').value = user.id;
        document.getElementById('edit-email').value = user.email;
        document.getElementById('edit-verified').checked = user.is_verified;
        document.getElementById('edit-admin').checked = user.is_admin;
        document.getElementById('edit-password').value = '';

        modal.classList.remove('hidden');
    }

    showDeleteUserModal(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        const modal = document.getElementById('delete-user-modal');
        if (!modal) return;

        document.getElementById('delete-user-email').textContent = user.email;
        modal.setAttribute('data-user-id', userId);
        modal.classList.remove('hidden');
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    async handleCreateUser(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const userData = {
            email: formData.get('email'),
            password: formData.get('password'),
            is_verified: formData.get('is_verified') === 'on',
            is_admin: formData.get('is_admin') === 'on'
        };

        try {
            const response = await fetch('/api/admin/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create user');
            }

            this.hideModal('create-user-modal');
            this.showToast('User created successfully', 'success');
            this.loadUsers();
            
        } catch (error) {
            console.error('Error creating user:', error);
            this.showToast(error.message, 'error');
        }
    }

    async handleEditUser(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const userId = formData.get('user_id');
        const userData = {
            email: formData.get('email'),
            is_verified: formData.get('is_verified') === 'on',
            is_admin: formData.get('is_admin') === 'on'
        };

        // Only include password if provided
        const password = formData.get('password');
        if (password && password.trim()) {
            userData.password = password;
        }

        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update user');
            }

            this.hideModal('edit-user-modal');
            this.showToast('User updated successfully', 'success');
            this.loadUsers();
            
        } catch (error) {
            console.error('Error updating user:', error);
            this.showToast(error.message, 'error');
        }
    }

    async confirmDeleteUser() {
        const modal = document.getElementById('delete-user-modal');
        const userId = modal.getAttribute('data-user-id');
        
        if (!userId) return;

        try {
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete user');
            }

            this.hideModal('delete-user-modal');
            this.showToast('User deleted successfully', 'success');
            this.loadUsers();
            
        } catch (error) {
            console.error('Error deleting user:', error);
            this.showToast(error.message, 'error');
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `pointer-events-auto max-w-sm w-full bg-white shadow-lg rounded-lg border-l-4 ${
            type === 'success' ? 'border-green-400' : 
            type === 'error' ? 'border-red-400' : 'border-blue-400'
        }`;
        
        toast.innerHTML = `
            <div class="p-4">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <span class="text-lg">
                            ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
                        </span>
                    </div>
                    <div class="ml-3 w-0 flex-1">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500" onclick="this.parentElement.parentElement.parentElement.parentElement.remove()">
                            <span class="sr-only">Close</span>
                            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(toast);

        // Auto-remove success toasts after 3 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 3000);
        }
    }

    async logout() {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            localStorage.removeItem('access_token');
            window.location.href = '/admin/login';
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.usersPageManager = new UsersPageManager();
});