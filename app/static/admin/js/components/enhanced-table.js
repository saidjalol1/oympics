/**
 * EnhancedTable Component
 * 
 * Manages enhanced table displays with sorting, selection, and row actions.
 * Provides a professional, interactive table experience for entity lists.
 * 
 * Features:
 * - Sortable column headers with visual indicators
 * - Ascending/descending sort toggle
 * - Zebra striping for improved readability
 * - Row hover highlighting
 * - Bulk selection with "Select All" checkbox
 * - Row actions (edit, delete) with event emission
 * - Empty state display
 * - Responsive design with Tailwind CSS
 * 
 * Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 15.1, 15.2, 15.3, 15.5
 */

class EnhancedTable {
    /**
     * Initialize the EnhancedTable component
     * @param {string} containerId - ID of the container element for the table
     * @param {Array<Object>} columns - Column definitions
     * @param {Object} options - Configuration options
     * @param {boolean} options.selectable - Enable bulk selection (default: false)
     * @param {boolean} options.actions - Show row actions (default: true)
     * @param {string} options.emptyMessage - Message to display when no data (default: "No data available")
     * @param {string} options.idField - Field name for row ID (default: "id")
     */
    constructor(containerId, columns = [], options = {}) {
        this.containerId = containerId;
        this.columns = columns;
        this.options = {
            selectable: options.selectable || false,
            actions: options.actions !== false,
            emptyMessage: options.emptyMessage || 'No data available',
            idField: options.idField || 'id'
        };
        
        this.data = [];
        this.sortColumn = null;
        this.sortDirection = 'asc'; // 'asc' or 'desc'
        this.selectedRows = new Set();
        
        this.listeners = {
            rowEdit: [],
            rowDelete: [],
            rowSelect: [],
            sortChange: [],
            rowClick: []
        };
        
        this.render();
    }
    
    /**
     * Set table data and render
     * @param {Array<Object>} data - Array of data objects
     */
    setData(data) {
        this.data = Array.isArray(data) ? data : [];
        this.selectedRows.clear();
        this.render();
    }
    
    /**
     * Sort data by column
     * @param {string} columnKey - Column key to sort by
     * @param {string} direction - Sort direction ('asc' or 'desc')
     */
    sort(columnKey, direction = null) {
        const column = this.columns.find(col => col.key === columnKey);
        
        if (!column || column.sortable === false) {
            return;
        }
        
        // Toggle direction if same column, or use provided direction
        if (direction) {
            this.sortDirection = direction;
        } else if (this.sortColumn === columnKey) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortDirection = 'asc';
        }
        
        this.sortColumn = columnKey;
        
        // Sort the data
        this.data.sort((a, b) => {
            let aVal = a[columnKey];
            let bVal = b[columnKey];
            
            // Handle null/undefined values
            if (aVal == null) return 1;
            if (bVal == null) return -1;
            
            // Detect data type and sort accordingly
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return this.sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
            }
            
            // Try to parse as date
            const aDate = new Date(aVal);
            const bDate = new Date(bVal);
            if (!isNaN(aDate) && !isNaN(bDate)) {
                return this.sortDirection === 'asc' ? aDate - bDate : bDate - aDate;
            }
            
            // Default to string comparison
            const aStr = String(aVal).toLowerCase();
            const bStr = String(bVal).toLowerCase();
            
            if (this.sortDirection === 'asc') {
                return aStr.localeCompare(bStr);
            } else {
                return bStr.localeCompare(aStr);
            }
        });
        
        // Re-render table
        this.render();
        
        // Emit sort change event
        this.emit('sortChange', {
            column: columnKey,
            direction: this.sortDirection
        });
    }
    
    /**
     * Get selected row data
     * @returns {Array<Object>} Array of selected row objects
     */
    getSelectedRows() {
        return this.data.filter(row => this.selectedRows.has(row[this.options.idField]));
    }
    
    /**
     * Clear all selections
     */
    clearSelection() {
        this.selectedRows.clear();
        this.render();
    }
    
    /**
     * Toggle row selection
     * @param {*} rowId - Row ID to toggle
     */
    toggleRowSelection(rowId) {
        if (this.selectedRows.has(rowId)) {
            this.selectedRows.delete(rowId);
        } else {
            this.selectedRows.add(rowId);
        }
        
        this.updateSelectionUI();
        
        // Emit selection event
        this.emit('rowSelect', {
            selectedIds: Array.from(this.selectedRows),
            selectedRows: this.getSelectedRows()
        });
    }
    
    /**
     * Toggle all rows selection
     */
    toggleSelectAll() {
        const allSelected = this.selectedRows.size === this.data.length && this.data.length > 0;
        
        if (allSelected) {
            this.selectedRows.clear();
        } else {
            this.data.forEach(row => {
                this.selectedRows.add(row[this.options.idField]);
            });
        }
        
        this.updateSelectionUI();
        
        // Emit selection event
        this.emit('rowSelect', {
            selectedIds: Array.from(this.selectedRows),
            selectedRows: this.getSelectedRows()
        });
    }
    
    /**
     * Update selection UI (checkboxes and count)
     */
    updateSelectionUI() {
        // Update select all checkbox
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.checked = this.selectedRows.size === this.data.length && this.data.length > 0;
            selectAllCheckbox.indeterminate = this.selectedRows.size > 0 && this.selectedRows.size < this.data.length;
        }
        
        // Update individual checkboxes
        this.data.forEach(row => {
            const rowId = row[this.options.idField];
            const checkbox = document.getElementById(`row-checkbox-${rowId}`);
            if (checkbox) {
                checkbox.checked = this.selectedRows.has(rowId);
            }
        });
        
        // Update selected count display
        const countDisplay = document.getElementById('selected-count');
        if (countDisplay) {
            if (this.selectedRows.size > 0) {
                countDisplay.textContent = `${this.selectedRows.size} selected`;
                countDisplay.classList.remove('hidden');
            } else {
                countDisplay.classList.add('hidden');
            }
        }
    }
    
    /**
     * Render the table
     */
    render() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`Container with ID "${this.containerId}" not found`);
            return;
        }
        
        // Show empty state if no data
        if (this.data.length === 0) {
            container.innerHTML = this.renderEmptyState();
            return;
        }
        
        const html = `
            <div class="enhanced-table-component">
                ${this.options.selectable ? this.renderSelectionToolbar() : ''}
                <div class="overflow-x-auto shadow-sm rounded-lg border border-gray-200">
                    <table class="min-w-full divide-y divide-gray-200">
                        ${this.renderHeader()}
                        ${this.renderBody()}
                    </table>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
        // Attach event listeners after rendering
        this.attachEventListeners();
        
        // Emit render event for external listeners
        this.emit('render');
    }
    
    /**
     * Render selection toolbar
     * @returns {string} HTML string for selection toolbar
     */
    renderSelectionToolbar() {
        return `
            <div class="mb-3 flex items-center justify-between">
                <div id="selected-count" class="hidden text-sm font-medium text-gray-700">
                    0 selected
                </div>
            </div>
        `;
    }
    
    /**
     * Render table header
     * @returns {string} HTML string for table header
     */
    renderHeader() {
        const selectionHeader = this.options.selectable ? `
            <th scope="col" class="w-12 px-4 py-3 bg-gray-50">
                <input 
                    type="checkbox" 
                    id="select-all-checkbox"
                    class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                    aria-label="Select all rows"
                />
            </th>
        ` : '';
        
        const columnHeaders = this.columns.map(column => {
            const isSortable = column.sortable !== false;
            const isSorted = this.sortColumn === column.key;
            const sortIcon = isSorted 
                ? (this.sortDirection === 'asc' ? '↑' : '↓')
                : '';
            
            const headerClasses = `
                px-4 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider bg-gray-50
                ${isSortable ? 'cursor-pointer hover:bg-gray-100 select-none' : ''}
            `.trim();
            
            return `
                <th 
                    scope="col" 
                    class="${headerClasses}"
                    ${isSortable ? `data-sort-key="${column.key}"` : ''}
                    ${isSortable ? 'role="button" tabindex="0"' : ''}
                    aria-label="${column.label}${isSortable ? ' (sortable)' : ''}"
                    ${isSorted ? `aria-sort="${this.sortDirection === 'asc' ? 'ascending' : 'descending'}"` : ''}
                >
                    <div class="flex items-center space-x-1">
                        <span>${column.label}</span>
                        ${isSortable ? `<span class="text-gray-400 font-bold">${sortIcon || '⇅'}</span>` : ''}
                    </div>
                </th>
            `;
        }).join('');
        
        const actionsHeader = this.options.actions ? `
            <th scope="col" class="w-24 px-4 py-3 text-right text-xs font-medium text-gray-700 uppercase tracking-wider bg-gray-50">
                Actions
            </th>
        ` : '';
        
        return `
            <thead>
                <tr>
                    ${selectionHeader}
                    ${columnHeaders}
                    ${actionsHeader}
                </tr>
            </thead>
        `;
    }
    
    /**
     * Render table body
     * @returns {string} HTML string for table body
     */
    renderBody() {
        const rows = this.data.map((row, index) => {
            const rowId = row[this.options.idField];
            const isSelected = this.selectedRows.has(rowId);
            
            // Zebra striping
            const rowClasses = `
                ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                hover:bg-blue-50 transition-colors duration-150
                ${isSelected ? 'bg-blue-100 hover:bg-blue-100' : ''}
            `.trim();
            
            const selectionCell = this.options.selectable ? `
                <td class="px-4 py-3">
                    <input 
                        type="checkbox" 
                        id="row-checkbox-${rowId}"
                        class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 cursor-pointer"
                        ${isSelected ? 'checked' : ''}
                        data-row-id="${rowId}"
                        aria-label="Select row"
                    />
                </td>
            ` : '';
            
            const dataCells = this.columns.map(column => {
                let value = row[column.key];
                
                // Use custom render function if provided
                if (column.render && typeof column.render === 'function') {
                    value = column.render(value, row);
                } else if (value == null) {
                    value = '-';
                }
                
                return `
                    <td class="px-4 py-3 text-sm text-gray-900">
                        ${value}
                    </td>
                `;
            }).join('');
            
            const actionsCell = this.options.actions ? `
                <td class="px-4 py-3 text-right text-sm flex items-center justify-end gap-2">
                    <button 
                        type="button"
                        class="inline-flex items-center px-2 py-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                        data-action="edit"
                        data-row-id="${rowId}"
                        aria-label="Edit row"
                    >
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                    </button>
                    <button 
                        type="button"
                        class="inline-flex items-center px-2 py-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
                        data-action="delete"
                        data-row-id="${rowId}"
                        aria-label="Delete row"
                    >
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                    </button>
                </td>
            ` : '';
            
            return `
                <tr class="${rowClasses}" data-row-id="${rowId}">
                    ${selectionCell}
                    ${dataCells}
                    ${actionsCell}
                </tr>
            `;
        }).join('');
        
        return `
            <tbody class="divide-y divide-gray-200">
                ${rows}
            </tbody>
        `;
    }
    
    /**
     * Render empty state
     * @returns {string} HTML string for empty state
     */
    renderEmptyState() {
        return `
            <div class="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
                <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p class="mt-4 text-sm text-gray-600">${this.options.emptyMessage}</p>
            </div>
        `;
    }
    
    /**
     * Attach event listeners to table elements
     */
    attachEventListeners() {
        // Sort column headers
        const sortableHeaders = document.querySelectorAll('[data-sort-key]');
        sortableHeaders.forEach(header => {
            const columnKey = header.getAttribute('data-sort-key');
            
            header.addEventListener('click', () => {
                this.sort(columnKey);
            });
            
            // Keyboard accessibility
            header.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.sort(columnKey);
                }
            });
        });
        
        // Select all checkbox
        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        if (selectAllCheckbox) {
            selectAllCheckbox.addEventListener('change', () => {
                this.toggleSelectAll();
            });
        }
        
        // Individual row checkboxes
        const rowCheckboxes = document.querySelectorAll('[data-row-id][type="checkbox"]');
        rowCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const rowId = parseInt(e.target.getAttribute('data-row-id'));
                this.toggleRowSelection(rowId);
            });
        });
        
        // Action buttons
        const actionButtons = document.querySelectorAll('[data-action]');
        actionButtons.forEach(button => {
            const action = button.getAttribute('data-action');
            const rowId = parseInt(button.getAttribute('data-row-id'));
            
            button.addEventListener('click', () => {
                const row = this.data.find(r => r[this.options.idField] === rowId);
                
                if (action === 'edit') {
                    this.emit('rowEdit', { id: rowId, row });
                } else if (action === 'delete') {
                    this.emit('rowDelete', { id: rowId, row });
                }
            });
        });
        
        // Row click handling for navigation
        if (this.options.clickableRows) {
            const tableRows = document.querySelectorAll('tbody tr');
            console.log('Setting up row click handlers for', tableRows.length, 'rows');
            tableRows.forEach(row => {
                row.addEventListener('click', (e) => {
                    console.log('Row clicked, target:', e.target.tagName);
                    // Don't trigger if clicking on buttons, checkboxes, or action elements
                    if (e.target.closest('[data-action]') || 
                        e.target.closest('input[type="checkbox"]') ||
                        e.target.closest('button')) {
                        console.log('Ignoring click on action element');
                        return;
                    }
                    
                    // Get the row ID from the data attribute
                    const rowId = parseInt(row.getAttribute('data-row-id'));
                    console.log('Row ID:', rowId);
                    const rowData = this.data.find(r => r[this.options.idField] === rowId);
                    console.log('Row data found:', rowData);
                    
                    if (rowData) {
                        console.log('Emitting rowClick event');
                        this.emit('rowClick', { id: rowId, row: rowData });
                    }
                });
            });
        }
    }
    
    /**
     * Register an event listener
     * @param {string} event - Event name (rowEdit, rowDelete, rowSelect, sortChange)
     * @param {Function} callback - Callback function to execute
     */
    on(event, callback) {
        if (this.listeners[event] && typeof callback === 'function') {
            this.listeners[event].push(callback);
        }
    }
    
    /**
     * Emit an event to all registered listeners
     * @param {string} event - Event name
     * @param {*} data - Data to pass to listeners
     */
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in ${event} listener:`, error);
                }
            });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedTable;
}
