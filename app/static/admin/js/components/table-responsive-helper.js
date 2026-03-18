/**
 * Table Responsive Helper
 * Converts tables to card-based layouts on mobile devices
 * Requirement: 14.6 - Card-based table layouts on mobile
 */

(function() {
    'use strict';

    /**
     * Convert table data to mobile card view
     * @param {Array} data - Array of data objects
     * @param {Array} columns - Array of column definitions
     * @param {Object} options - Options for card rendering
     * @returns {string} HTML string for mobile cards
     */
    function createMobileCards(data, columns, options = {}) {
        if (!data || !data.length) {
            return '<div class="text-center py-8 text-gray-500">No data available</div>';
        }

        const cards = data.map(item => createMobileCard(item, columns, options));
        return `<div class="mobile-card-view">${cards.join('')}</div>`;
    }

    /**
     * Create a single mobile card
     * @param {Object} item - Data item
     * @param {Array} columns - Column definitions
     * @param {Object} options - Options for card rendering
     * @returns {string} HTML string for a single card
     */
    function createMobileCard(item, columns, options = {}) {
        const { onEdit, onDelete, onView, primaryKey = 'id' } = options;
        
        // Get primary field for header (usually first visible column)
        const headerColumn = columns.find(col => !col.hidden && col.key !== primaryKey);
        const headerValue = headerColumn ? formatValue(item[headerColumn.key], headerColumn) : 'Item';

        // Create rows for each column (except actions)
        const rows = columns
            .filter(col => !col.hidden && col.key !== 'actions')
            .map(col => {
                const label = col.label || col.key;
                const value = formatValue(item[col.key], col);
                
                return `
                    <div class="mobile-card-row">
                        <span class="mobile-card-label">${escapeHtml(label)}</span>
                        <span class="mobile-card-value">${value}</span>
                    </div>
                `;
            })
            .join('');

        // Create action buttons
        const actions = [];
        if (onView) {
            actions.push(`
                <button 
                    class="flex-1 px-3 py-2 bg-blue-500 text-white rounded text-sm hover:bg-blue-600 transition-colors"
                    onclick="(${onView.toString()})(${item[primaryKey]})"
                >
                    View
                </button>
            `);
        }
        if (onEdit) {
            actions.push(`
                <button 
                    class="flex-1 px-3 py-2 bg-green-500 text-white rounded text-sm hover:bg-green-600 transition-colors"
                    onclick="(${onEdit.toString()})(${item[primaryKey]})"
                >
                    Edit
                </button>
            `);
        }
        if (onDelete) {
            actions.push(`
                <button 
                    class="flex-1 px-3 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600 transition-colors"
                    onclick="(${onDelete.toString()})(${item[primaryKey]})"
                >
                    Delete
                </button>
            `);
        }

        const actionsHtml = actions.length > 0 
            ? `<div class="mobile-card-actions">${actions.join('')}</div>`
            : '';

        return `
            <div class="mobile-card" data-id="${item[primaryKey]}">
                <div class="mobile-card-header">${escapeHtml(headerValue)}</div>
                ${rows}
                ${actionsHtml}
            </div>
        `;
    }

    /**
     * Format value based on column type
     * @param {*} value - Value to format
     * @param {Object} column - Column definition
     * @returns {string} Formatted value
     */
    function formatValue(value, column) {
        if (value === null || value === undefined) {
            return '<span class="text-gray-400">—</span>';
        }

        // Custom formatter
        if (column.formatter && typeof column.formatter === 'function') {
            return column.formatter(value);
        }

        // Type-based formatting
        switch (column.type) {
            case 'date':
                return formatDate(value);
            case 'datetime':
                return formatDateTime(value);
            case 'currency':
                return formatCurrency(value);
            case 'boolean':
                return formatBoolean(value);
            case 'badge':
                return formatBadge(value, column.badgeColors);
            default:
                return escapeHtml(String(value));
        }
    }

    /**
     * Format date value
     */
    function formatDate(value) {
        try {
            const date = new Date(value);
            return date.toLocaleDateString();
        } catch (e) {
            return escapeHtml(String(value));
        }
    }

    /**
     * Format datetime value
     */
    function formatDateTime(value) {
        try {
            const date = new Date(value);
            return date.toLocaleString();
        } catch (e) {
            return escapeHtml(String(value));
        }
    }

    /**
     * Format currency value
     */
    function formatCurrency(value) {
        if (value === 0 || value === '0.00') {
            return '<span class="text-green-600 font-medium">Free</span>';
        }
        try {
            const num = parseFloat(value);
            return `<span class="font-medium">$${num.toFixed(2)}</span>`;
        } catch (e) {
            return escapeHtml(String(value));
        }
    }

    /**
     * Format boolean value
     */
    function formatBoolean(value) {
        if (value === true || value === 'true' || value === 1) {
            return '<span class="text-green-600">✓ Yes</span>';
        }
        return '<span class="text-red-600">✗ No</span>';
    }

    /**
     * Format badge value
     */
    function formatBadge(value, colors = {}) {
        const color = colors[value] || 'gray';
        const colorClasses = {
            green: 'bg-green-100 text-green-800',
            red: 'bg-red-100 text-red-800',
            blue: 'bg-blue-100 text-blue-800',
            yellow: 'bg-yellow-100 text-yellow-800',
            gray: 'bg-gray-100 text-gray-800'
        };
        const classes = colorClasses[color] || colorClasses.gray;
        return `<span class="inline-block px-2 py-1 rounded text-xs font-medium ${classes}">${escapeHtml(String(value))}</span>`;
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Check if current viewport is mobile
     */
    function isMobileView() {
        return window.innerWidth < 768;
    }

    /**
     * Toggle between table and card view based on screen size
     */
    function updateResponsiveView(tableElement, data, columns, options) {
        if (!tableElement) return;

        const container = tableElement.parentElement;
        if (!container) return;

        if (isMobileView()) {
            // Hide table, show cards
            tableElement.classList.add('desktop-table');
            
            // Check if mobile view already exists
            let mobileView = container.querySelector('.mobile-card-view');
            if (!mobileView) {
                const cardsHtml = createMobileCards(data, columns, options);
                const mobileDiv = document.createElement('div');
                mobileDiv.innerHTML = cardsHtml;
                container.appendChild(mobileDiv.firstElementChild);
            }
        } else {
            // Show table, hide cards
            tableElement.classList.remove('desktop-table');
            const mobileView = container.querySelector('.mobile-card-view');
            if (mobileView) {
                mobileView.remove();
            }
        }
    }

    // Expose functions globally
    window.TableResponsiveHelper = {
        createMobileCards,
        createMobileCard,
        formatValue,
        isMobileView,
        updateResponsiveView,
        escapeHtml
    };
})();
