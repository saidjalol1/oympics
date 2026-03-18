/**
 * User Management Module
 * Handles user CRUD operations and display
 */

const UserManagement = {
    // Load and display users
    async loadUsers() {
        UIUtils.showLoading();
        
        try {
            const verifiedOnly = state.verifiedFilter === '' ? null : 
                                state.verifiedFilter === 'true' ? true :
                                state.verifiedFilter === 'false' ? false : null;
            
            const isAdmin = state.adminFilter === '' ? null : 
                           state.adminFilter === 'true' ? true :
                           state.adminFilter === 'false' ? false : null;
            
            const response = await apiClient.getUsers(
                state.currentPage * state.pageSize,
                state.pageSize,
                state.searchQuery,
                verifiedOnly,
                isAdmin
            );
            
            // Ensure response has the expected structure
            if (!response || typeof response !== 'object') {
                throw new Error('Invalid response format from server');
            }
            
            state.users = response.users || [];
            state.totalUsers = response.total || 0;
            
            this.updateFilterDisplay();
            
            if (state.users.length === 0) {
                UIUtils.showEmpty();
            } else {
                this.renderUserTable();
                this.updatePagination();
                UIUtils.showTable();
            }
        } catch (error) {
            console.error('Error loading users:', error);
            UIUtils.showError(UIUtils.parseError(error));
        }
    },

    // Render user table
    renderUserTable() {
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = '';
        
        state.users.forEach(user => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 transition-colors';
            
            const verifiedBadge = user.is_verified 
                ? '<span class="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Verified</span>'
                : '<span class="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">Unverified</span>';
            
            const adminBadge = user.is_admin
                ? '<span class="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Admin</span>'
                : '';
            
            row.innerHTML = `
                <td class="px-6 py-4 text-sm text-gray-900">${user.id}</td>
                <td class="px-6 py-4 text-sm text-gray-900">${user.email}</td>
                <td class="px-6 py-4 text-sm">${verifiedBadge}</td>
                <td class="px-6 py-4 text-sm">${adminBadge}</td>
                <td class="px-6 py-4 text-sm text-gray-500">${UIUtils.formatDate(user.created_at)}</td>
                <td class="px-6 py-4 text-sm space-x-2">
                    <button class="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors" data-action="edit-user" data-user-id="${user.id}">
                        Edit
                    </button>
                    <button class="px-2 py-1 bg-yellow-500 text-white rounded text-xs hover:bg-yellow-600 transition-colors" data-action="toggle-verify" data-user-id="${user.id}">
                        ${user.is_verified ? 'Unverify' : 'Verify'}
                    </button>
                    <button class="px-2 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600 transition-colors" data-action="delete-user" data-user-id="${user.id}">
                        Delete
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    },

    // Update pagination display
    updatePagination() {
        const start = state.currentPage * state.pageSize + 1;
        const end = Math.min((state.currentPage + 1) * state.pageSize, state.totalUsers);
        
        document.getElementById('page-start').textContent = state.totalUsers === 0 ? 0 : start;
        document.getElementById('page-end').textContent = end;
        document.getElementById('total-count').textContent = state.totalUsers;
        
        const prevBtn = document.getElementById('prev-page-btn');
        const nextBtn = document.getElementById('next-page-btn');
        
        prevBtn.disabled = state.currentPage === 0;
        nextBtn.disabled = end >= state.totalUsers;
    },

    // Update filter display
    updateFilterDisplay() {
        const filterBadges = document.getElementById('filter-badges');
        const activeFiltersContainer = document.getElementById('active-filters');
        filterBadges.innerHTML = '';
        
        const filters = [];
        
        if (state.searchQuery) {
            filters.push(`Search: "${state.searchQuery}"`);
        }
        
        if (state.verifiedFilter === 'true') {
            filters.push('Verified Users');
        } else if (state.verifiedFilter === 'false') {
            filters.push('Unverified Users');
        }
        
        if (state.adminFilter === 'true') {
            filters.push('Admin Users');
        } else if (state.adminFilter === 'false') {
            filters.push('Regular Users');
        }
        
        if (filters.length > 0) {
            activeFiltersContainer.classList.remove('hidden');
            filters.forEach(filter => {
                const badge = document.createElement('span');
                badge.className = 'px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full';
                badge.textContent = filter;
                filterBadges.appendChild(badge);
            });
        } else {
            activeFiltersContainer.classList.add('hidden');
        }
    },

    // Create user
    async createUser(email, password, isVerified, isAdmin) {
        try {
            await apiClient.createUser(email, password, isVerified, isAdmin);
            UIUtils.closeModal('create-user-modal');
            UIUtils.showToast('User created successfully', 'success');
            state.resetPagination();
            await this.loadUsers();
        } catch (error) {
            UIUtils.showToast(UIUtils.parseError(error), 'error');
        }
    },

    // Update user
    async updateUser(userId, updates) {
        try {
            await apiClient.updateUser(userId, updates);
            UIUtils.closeModal('edit-user-modal');
            UIUtils.showToast('User updated successfully', 'success');
            await this.loadUsers();
        } catch (error) {
            UIUtils.showToast(UIUtils.parseError(error), 'error');
        }
    },

    // Delete user
    async deleteUser(userId) {
        try {
            await apiClient.deleteUser(userId);
            UIUtils.closeModal('delete-user-modal');
            UIUtils.showToast('User deleted successfully', 'success');
            state.deleteUserId = null;
            await this.loadUsers();
        } catch (error) {
            UIUtils.showToast(UIUtils.parseError(error), 'error');
        }
    },

    // Toggle verification
    async toggleVerification(userId) {
        try {
            await apiClient.toggleVerification(userId);
            UIUtils.showToast('Verification status updated', 'success');
            await this.loadUsers();
        } catch (error) {
            UIUtils.showToast(UIUtils.parseError(error), 'error');
        }
    }
};
