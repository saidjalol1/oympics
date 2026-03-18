/**
 * Event Handlers Module
 * Manages all DOM event listeners
 */

const EventHandlers = {
    init() {
        this.setupSearchAndFilters();
        this.setupPagination();
        this.setupUserCreation();
        this.setupUserEdit();
        this.setupUserDeletion();
        this.setupVerificationToggle();
        this.setupModalControls();
        this.setupLogout();
        this.setupNavigation();
        this.setupAuditPagination();
        this.setupAuditDetails();
    },

    // Search and Filter Events
    setupSearchAndFilters() {
        let searchTimeout;

        document.getElementById('search-input').addEventListener('input', (e) => {
            state.searchQuery = e.target.value;
            state.resetPagination();
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => UserManagement.loadUsers(), 300);
        });

        document.getElementById('verified-filter').addEventListener('change', (e) => {
            state.verifiedFilter = e.target.value;
            state.resetPagination();
            UserManagement.loadUsers();
        });

        document.getElementById('admin-filter').addEventListener('change', (e) => {
            state.adminFilter = e.target.value;
            state.resetPagination();
            UserManagement.loadUsers();
        });

        document.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'clear-filters') {
                state.resetFilters();
                
                document.getElementById('search-input').value = '';
                document.getElementById('verified-filter').value = '';
                document.getElementById('admin-filter').value = '';
                
                UserManagement.loadUsers();
            }
        });
    },

    // Pagination Events
    setupPagination() {
        document.getElementById('page-size').addEventListener('change', (e) => {
            state.pageSize = parseInt(e.target.value);
            state.resetPagination();
            UserManagement.loadUsers();
        });

        document.getElementById('prev-page-btn').addEventListener('click', () => {
            if (state.currentPage > 0) {
                state.currentPage--;
                UserManagement.loadUsers();
            }
        });

        document.getElementById('next-page-btn').addEventListener('click', () => {
            const maxPage = Math.ceil(state.totalUsers / state.pageSize) - 1;
            if (state.currentPage < maxPage) {
                state.currentPage++;
                UserManagement.loadUsers();
            }
        });
    },

    // User Creation Events
    setupUserCreation() {
        document.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'create-user') {
                document.getElementById('create-user-form').reset();
                UIUtils.openModal('create-user-modal');
            }
        });

        document.getElementById('create-user-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('create-email').value.trim();
            const password = document.getElementById('create-password').value;
            const isVerified = document.getElementById('create-verified').checked;
            const isAdmin = document.getElementById('create-admin').checked;
            
            if (!email || !password) {
                UIUtils.showToast('Please fill in all required fields', 'error');
                return;
            }
            
            if (password.length < 8) {
                UIUtils.showToast('Password must be at least 8 characters', 'error');
                return;
            }
            
            await UserManagement.createUser(email, password, isVerified, isAdmin);
        });
    },

    // User Edit Events
    setupUserEdit() {
        document.addEventListener('click', async (e) => {
            if (e.target.dataset.action === 'edit-user') {
                const userId = parseInt(e.target.dataset.userId);
                const user = state.users.find(u => u.id === userId);
                
                if (user) {
                    document.getElementById('edit-user-id').value = user.id;
                    document.getElementById('edit-email').value = user.email;
                    document.getElementById('edit-password').value = '';
                    document.getElementById('edit-verified').checked = user.is_verified;
                    document.getElementById('edit-admin').checked = user.is_admin;
                    UIUtils.openModal('edit-user-modal');
                }
            }
        });

        document.getElementById('edit-user-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const userId = parseInt(document.getElementById('edit-user-id').value);
            const email = document.getElementById('edit-email').value.trim();
            const password = document.getElementById('edit-password').value;
            const isVerified = document.getElementById('edit-verified').checked;
            const isAdmin = document.getElementById('edit-admin').checked;
            
            if (!email) {
                UIUtils.showToast('Email is required', 'error');
                return;
            }
            
            if (password && password.length < 8) {
                UIUtils.showToast('Password must be at least 8 characters', 'error');
                return;
            }
            
            const updates = {
                email: email,
                is_verified: isVerified,
                is_admin: isAdmin
            };
            
            if (password) {
                updates.password = password;
            }
            
            await UserManagement.updateUser(userId, updates);
        });
    },

    // User Deletion Events
    setupUserDeletion() {
        document.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'delete-user') {
                const userId = parseInt(e.target.dataset.userId);
                const user = state.users.find(u => u.id === userId);
                
                if (user) {
                    state.deleteUserId = userId;
                    document.getElementById('delete-user-email').textContent = user.email;
                    UIUtils.openModal('delete-user-modal');
                }
            }
        });

        document.addEventListener('click', async (e) => {
            if (e.target.dataset.action === 'confirm-delete') {
                if (state.deleteUserId === null) return;
                await UserManagement.deleteUser(state.deleteUserId);
            }
        });
    },

    // Verification Toggle Events
    setupVerificationToggle() {
        document.addEventListener('click', async (e) => {
            if (e.target.dataset.action === 'toggle-verify') {
                const userId = parseInt(e.target.dataset.userId);
                await UserManagement.toggleVerification(userId);
            }
        });
    },

    // Modal Control Events
    setupModalControls() {
        document.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'close-modal') {
                const modalId = e.target.dataset.modal;
                UIUtils.closeModal(modalId);
            }
        });
    },

    // Logout Events
    setupLogout() {
        document.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'logout' || e.target.dataset.action === 'logout-from-modal') {
                EventHandlers.performLogout();
            }
        });
    },

    // Perform logout
    performLogout: async function() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            });
            
            window.location.href = '/admin/login';
        } catch (error) {
            window.location.href = '/admin/login';
        }
    },

    // Navigation Events
    setupNavigation() {
        document.addEventListener('click', (e) => {
            if (e.target.dataset.nav === 'users') {
                e.preventDefault();
                EventHandlers.showUsersPage();
            }
            if (e.target.dataset.nav === 'audit-logs') {
                e.preventDefault();
                EventHandlers.showAuditPage();
            }
            if (e.target.dataset.nav === 'test-management') {
                e.preventDefault();
                EventHandlers.showTestManagementPage();
            }
        });
    },

    showUsersPage() {
        document.getElementById('users-page').classList.remove('hidden');
        document.getElementById('audit-page').classList.add('hidden');
        document.querySelector('[data-nav="users"]').classList.add('bg-blue-500', 'text-white');
        document.querySelector('[data-nav="users"]').classList.remove('text-gray-700');
        document.querySelector('[data-nav="audit-logs"]').classList.remove('bg-blue-500', 'text-white');
        document.querySelector('[data-nav="audit-logs"]').classList.add('text-gray-700');
    },

    showAuditPage() {
        document.getElementById('users-page').classList.add('hidden');
        document.getElementById('audit-page').classList.remove('hidden');
        document.querySelector('[data-nav="audit-logs"]').classList.add('bg-blue-500', 'text-white');
        document.querySelector('[data-nav="audit-logs"]').classList.remove('text-gray-700');
        document.querySelector('[data-nav="users"]').classList.remove('bg-blue-500', 'text-white');
        document.querySelector('[data-nav="users"]').classList.add('text-gray-700');
        AuditManagement.loadAuditLogs();
    },

    showTestManagementPage() {
        document.getElementById('users-page').classList.add('hidden');
        document.getElementById('audit-page').classList.add('hidden');
        document.getElementById('test-management-page').classList.remove('hidden');
        
        document.querySelector('[data-nav="test-management"]').classList.add('bg-blue-500', 'text-white');
        document.querySelector('[data-nav="test-management"]').classList.remove('text-gray-700');
        document.querySelector('[data-nav="users"]').classList.remove('bg-blue-500', 'text-white');
        document.querySelector('[data-nav="users"]').classList.add('text-gray-700');
        document.querySelector('[data-nav="audit-logs"]').classList.remove('bg-blue-500', 'text-white');
        document.querySelector('[data-nav="audit-logs"]').classList.add('text-gray-700');
        
        document.getElementById('page-title').textContent = 'Test Management';
        document.getElementById('page-subtitle').textContent = 'Manage subjects, levels, tests, and questions';
        
        testMgmt.loadSubjects();
    },

    // Audit Pagination Events
    setupAuditPagination() {
        const prevBtn = document.getElementById('audit-prev-page-btn');
        const nextBtn = document.getElementById('audit-next-page-btn');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (AuditManagement.currentPage > 0) {
                    AuditManagement.currentPage--;
                    AuditManagement.loadAuditLogs();
                }
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                const maxPage = Math.ceil(AuditManagement.totalLogs / AuditManagement.pageSize) - 1;
                if (AuditManagement.currentPage < maxPage) {
                    AuditManagement.currentPage++;
                    AuditManagement.loadAuditLogs();
                }
            });
        }
    },

    // Audit Details Events
    setupAuditDetails() {
        document.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'view-audit-details') {
                const logId = parseInt(e.target.dataset.logId);
                const log = AuditManagement.getLogDetails(logId);
                
                if (log) {
                    document.getElementById('audit-details-id').textContent = log.id;
                    document.getElementById('audit-details-admin').textContent = log.admin_email;
                    document.getElementById('audit-details-action').textContent = log.action_type;
                    document.getElementById('audit-details-target').textContent = log.target_user_email || '-';
                    document.getElementById('audit-details-status').textContent = log.success ? 'Success' : 'Failed';
                    document.getElementById('audit-details-timestamp').textContent = UIUtils.formatDate(log.created_at);
                    document.getElementById('audit-details-details').textContent = log.details || 'No additional details';
                    UIUtils.openModal('audit-details-modal');
                }
            }
        });
    }
};
