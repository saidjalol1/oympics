/**
 * Audit Management Module
 * Handles audit logs display and filtering
 */

const AuditManagement = {
    currentPage: 0,
    pageSize: 25,
    actionTypeFilter: null,
    adminEmailFilter: null,
    totalLogs: 0,
    logsMap: {},
    
    async loadAuditLogs() {
        UIUtils.showLoading();
        
        try {
            const response = await ApiClient.getAuditLogs(
                this.currentPage * this.pageSize,
                this.pageSize,
                this.actionTypeFilter,
                this.adminEmailFilter
            );
            
            this.totalLogs = response.total;
            this.renderAuditTable(response.logs);
            this.updateAuditPagination();
            UIUtils.showTable();
        } catch (error) {
            UIUtils.showError(UIUtils.parseError(error));
        }
    },
    
    renderAuditTable(logs) {
        const tbody = document.getElementById('audit-logs-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        // Store logs in map for quick access
        this.logsMap = {};
        logs.forEach(log => {
            this.logsMap[log.id] = log;
        });
        
        logs.forEach(log => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 transition-colors';
            
            const actionBadge = this.getActionBadge(log.action_type);
            const statusBadge = log.success 
                ? '<span class="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Success</span>'
                : '<span class="inline-block px-2 py-1 bg-red-100 text-red-800 text-xs rounded">Failed</span>';
            
            row.innerHTML = `
                <td class="px-6 py-4 text-sm text-gray-900">${log.id}</td>
                <td class="px-6 py-4 text-sm text-gray-900">${log.admin_email}</td>
                <td class="px-6 py-4 text-sm">${actionBadge}</td>
                <td class="px-6 py-4 text-sm text-gray-900">${log.target_user_email || '-'}</td>
                <td class="px-6 py-4 text-sm">${statusBadge}</td>
                <td class="px-6 py-4 text-sm text-gray-500">${UIUtils.formatDate(log.created_at)}</td>
                <td class="px-6 py-4 text-sm">
                    <button class="px-2 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600 transition-colors" data-action="view-audit-details" data-log-id="${log.id}">
                        Details
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    },
    
    getActionBadge(actionType) {
        const badges = {
            'create_user': '<span class="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Create User</span>',
            'update_user': '<span class="inline-block px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">Update User</span>',
            'delete_user': '<span class="inline-block px-2 py-1 bg-red-100 text-red-800 text-xs rounded">Delete User</span>',
            'toggle_verification': '<span class="inline-block px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">Toggle Verify</span>',
            'login': '<span class="inline-block px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Login</span>',
            'logout': '<span class="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">Logout</span>',
        };
        return badges[actionType] || `<span class="inline-block px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">${actionType}</span>`;
    },
    
    updateAuditPagination() {
        const start = this.currentPage * this.pageSize + 1;
        const end = Math.min((this.currentPage + 1) * this.pageSize, this.totalLogs);
        
        const pageStart = document.getElementById('audit-page-start');
        const pageEnd = document.getElementById('audit-page-end');
        const totalCount = document.getElementById('audit-total-count');
        
        if (pageStart) pageStart.textContent = this.totalLogs === 0 ? 0 : start;
        if (pageEnd) pageEnd.textContent = end;
        if (totalCount) totalCount.textContent = this.totalLogs;
        
        const prevBtn = document.getElementById('audit-prev-page-btn');
        const nextBtn = document.getElementById('audit-next-page-btn');
        
        if (prevBtn) prevBtn.disabled = this.currentPage === 0;
        if (nextBtn) nextBtn.disabled = end >= this.totalLogs;
    },
    
    getLogDetails(logId) {
        return this.logsMap[logId] || null;
    }
};
