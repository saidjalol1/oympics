/**
 * State Management Module
 * Centralized state for the admin panel
 */

const state = {
    currentPage: 0,
    pageSize: 25,
    searchQuery: '',
    verifiedFilter: '',
    adminFilter: '',
    totalUsers: 0,
    users: [],
    deleteUserId: null,
    currentUserEmail: null,
    isLoading: false,
    
    // Reset filters
    resetFilters() {
        this.searchQuery = '';
        this.verifiedFilter = '';
        this.adminFilter = '';
        this.currentPage = 0;
    },
    
    // Reset pagination
    resetPagination() {
        this.currentPage = 0;
    }
};
