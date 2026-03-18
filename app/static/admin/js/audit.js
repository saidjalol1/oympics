/**
 * Audit Page Management
 * Handles audit log viewing for the dedicated audit page
 */

class AuditPageManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 25;
        this.totalCount = 0;
        this.currentFilters = {};
        this.auditLogs = [];
        this.admins = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadAdmins();
        this.loadAuditLogs();
        
        // Load current user info
        this.loadCurrentUser();
    }

    setupEventListeners() {
        // Filter controls
        const adminFilter = document.getElementById('admin-filter');
        const actionFilter = document.getElementById('action-filter');
        const dateFromFilter = document.getElementById('date-from');
        const dateToFilter = document.getElementById('date-to');
        
        if (adminFilter) {
            adminFilter.addEventListener('change', (e) => {
                this.handleFilter('admin_id', e.target.value);
            });
        }
        
        if (actionFilter) {
            actionFilter.addEventListener('change', (e) => {
                this.handleFilter('action', e.target.value);
            });
        }
        
        if (dateFromFilter) {
            dateFromFilter.addEventListener('change', (e) => {
                this.handleFilter('date_from', e.target.value);
            });
        }
        
        if (dateToFilter) {
            dateToFilter.addEventListener('change', (e) => {
                this.handleFilter('date_to', e.target.value);
            });
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
                this.loadAuditLogs();
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

    async loadAdmins() {
        try {
            const response = await fetch('/api/admin/users?admin=true&size=1000', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.admins = data.items || [];
                this.populateAdminFilter();
            }
        } catch (error) {
            console.error('Error loading admins:', error);
        }
    }

    populateAdminFilter() {
        const adminFilter = document.getElementById('admin-filter');
        if (!adminFilter) return;

        // Clear existing options except the first one
        while (adminFilter.children.length > 1) {
            adminFilter.removeChild(adminFilter.lastChild);
        }

        // Add admin options
        this.admins.forEach(admin => {
            const option = document.createElement('option');
            option.value = admin.id;
            option.textContent = admin.email;
            adminFilter.appendChild(option);
        });
    }

    async loadAuditLogs() {
        this.showLoading();
        
        try {
            const skip = (this.currentPage - 1) * this.pageSize;
            const params = new URLSearchParams({
                skip: skip,
                limit: this.pageSize,
                ...this.currentFilters
            });

            const response = await fetch(`/api/admin/audit-logs?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.auditLogs = data.logs || [];
            this.totalCount = data.total || 0;
            
            this.renderAuditLogs();
            this.updatePagination();
            this.hideLoading();
            
        } catch (error) {
            console.error('Error loading audit logs:', error);
            this.showError('Failed to load audit logs. Please try again.');
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

    renderAuditLogs() {
        const tbody = document.getElementById('audit-logs-body');
        const tableContainer = document.getElementById('table-container');
        const emptyState = document.getElementById('empty-state');

        if (!tbody) return;

        if (this.auditLogs.length === 0) {
            tableContainer.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }

        tableContainer.classList.remove('hidden');
        emptyState.classList.add('hidden');

        tbody.innerHTML = this.auditLogs.map(log => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${log.id}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${log.admin_email || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getActionBadgeClass(log.action_type)}">
                        ${this.formatAction(log.action_type)}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${log.target_user_email || '-'}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full ${this.getStatusBadgeClass(log.success)}">
                        ${log.success ? 'SUCCESS' : 'FAILED'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${new Date(log.created_at).toLocaleString()}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button 
                        class="text-blue-600 hover:text-blue-900 transition-colors"
                        onclick="auditPageManager.showAuditDetailsModal(${log.id})"
                    >
                        View Details
                    </button>
                </td>
            </tr>
        `).join('');
    }

    getActionBadgeClass(action) {
        switch (action) {
            case 'CREATE_USER':
                return 'bg-green-100 text-green-800';
            case 'UPDATE_USER':
                return 'bg-blue-100 text-blue-800';
            case 'DELETE_USER':
                return 'bg-red-100 text-red-800';
            case 'LOGIN':
                return 'bg-purple-100 text-purple-800';
            case 'LOGOUT':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    }

    getStatusBadgeClass(success) {
        if (success === true) {
            return 'bg-green-100 text-green-800';
        } else if (success === false) {
            return 'bg-red-100 text-red-800';
        }
        return 'bg-gray-100 text-gray-800';
    }

    formatAction(action) {
        return action.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase());
    }

    updatePagination() {
        const paginationContainer = document.getElementById('pagination-container');
        const pageStart = document.getElementById('page-start');
        const pageEnd = document.getElementById('page-end');
        const totalCount = document.getElementById('total-count');
        const prevPageBtn = document.getElementById('prev-page-btn');
        const nextPageBtn = document.getElementById('next-page-btn');

        if (this.auditLogs.length === 0) {
            paginationContainer.classList.add('hidden');
            return;
        }

        paginationContainer.classList.remove('hidden');

        const start = (this.currentPage - 1) * this.pageSize + 1;
        const end = Math.min(start + this.auditLogs.length - 1, this.totalCount);

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

    handleFilter(type, value) {
        if (value) {
            this.currentFilters[type] = value;
        } else {
            delete this.currentFilters[type];
        }
        
        this.currentPage = 1;
        this.loadAuditLogs();
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
                    case 'admin_id':
                        const admin = this.admins.find(a => a.id.toString() === value);
                        label = `Admin: ${admin ? admin.email : value}`;
                        break;
                    case 'action':
                        label = `Action: ${this.formatAction(value)}`;
                        break;
                    case 'date_from':
                        label = `From: ${value}`;
                        break;
                    case 'date_to':
                        label = `To: ${value}`;
                        break;
                }
                
                return `<span class="inline-flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                    ${label}
                    <button class="ml-1 text-blue-600 hover:text-blue-800" onclick="auditPageManager.removeFilter('${key}')">×</button>
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
        if (key === 'admin_id') {
            const adminFilter = document.getElementById('admin-filter');
            if (adminFilter) adminFilter.value = '';
        } else if (key === 'action') {
            const actionFilter = document.getElementById('action-filter');
            if (actionFilter) actionFilter.value = '';
        } else if (key === 'date_from') {
            const dateFromFilter = document.getElementById('date-from');
            if (dateFromFilter) dateFromFilter.value = '';
        } else if (key === 'date_to') {
            const dateToFilter = document.getElementById('date-to');
            if (dateToFilter) dateToFilter.value = '';
        }
        
        this.currentPage = 1;
        this.loadAuditLogs();
        this.updateActiveFilters();
    }

    clearFilters() {
        this.currentFilters = {};
        
        // Reset UI controls
        const adminFilter = document.getElementById('admin-filter');
        const actionFilter = document.getElementById('action-filter');
        const dateFromFilter = document.getElementById('date-from');
        const dateToFilter = document.getElementById('date-to');
        
        if (adminFilter) adminFilter.value = '';
        if (actionFilter) actionFilter.value = '';
        if (dateFromFilter) dateFromFilter.value = '';
        if (dateToFilter) dateToFilter.value = '';
        
        this.currentPage = 1;
        this.loadAuditLogs();
        this.updateActiveFilters();
    }

    goToPreviousPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadAuditLogs();
        }
    }

    goToNextPage() {
        const maxPage = Math.ceil(this.totalCount / this.pageSize);
        if (this.currentPage < maxPage) {
            this.currentPage++;
            this.loadAuditLogs();
        }
    }

    showAuditDetailsModal(logId) {
        const log = this.auditLogs.find(l => l.id === logId);
        if (!log) return;

        const modal = document.getElementById('audit-details-modal');
        if (!modal) return;

        // Populate modal with log details
        document.getElementById('audit-details-id').textContent = log.id;
        document.getElementById('audit-details-admin').textContent = log.admin_email || '-';
        document.getElementById('audit-details-action').textContent = this.formatAction(log.action_type);
        document.getElementById('audit-details-target').textContent = log.target_user_email || '-';
        document.getElementById('audit-details-status').textContent = log.success ? 'SUCCESS' : 'FAILED';
        document.getElementById('audit-details-timestamp').textContent = new Date(log.created_at).toLocaleString();
        document.getElementById('audit-details-details').textContent = log.details || 'No additional details';

        modal.classList.remove('hidden');
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
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
    window.auditPageManager = new AuditPageManager();
});