# Admin UI Components

This directory contains reusable JavaScript components for the admin interface.

## LanguageSwitcher Component

### Overview
The LanguageSwitcher component manages multi-language support for the admin UI, allowing users to switch between English (EN), Uzbek (UZ), and Russian (RU).

### Features
- **Language Selection**: Dropdown selector with three language options
- **Persistence**: Saves language preference to localStorage
- **Auto-Update**: Automatically updates all UI elements with `data-i18n` attributes
- **Performance**: Updates UI within 200ms (Requirement 2.2)
- **Event System**: Emits `languageChanged` events for other components to listen
- **Fallback**: Falls back to English for missing translations (Requirement 2.6)

### Usage

#### Basic Setup
```javascript
// Initialize with translations object
const switcher = new LanguageSwitcher('language-switcher', translations);
```

#### HTML Integration
```html
<!-- Container for the language switcher -->
<div id="language-switcher"></div>

<!-- Elements with data-i18n attributes will be auto-updated -->
<h1 data-i18n="page.title">Page Title</h1>
<button data-i18n="action.save">Save</button>
<input type="text" data-i18n="placeholder.search" placeholder="Search...">
```

#### Listening to Language Changes
```javascript
switcher.on('languageChanged', (data) => {
    console.log(`Language changed to: ${data.language}`);
    console.log(`Update took: ${data.duration}ms`);
    
    // Reload data in new language
    reloadPageData();
});
```

#### API Methods

##### `constructor(containerId, translations)`
Initialize the language switcher.
- `containerId`: ID of the container element
- `translations`: Object with structure `{ en: {}, uz: {}, ru: {} }`

##### `getCurrentLanguage()`
Returns the current language code (`'en'`, `'uz'`, or `'ru'`).

##### `setLanguage(languageCode)`
Set the current language and update UI.
- `languageCode`: Language code to set

##### `loadLanguage()`
Load language preference from localStorage. Returns saved language or `'en'` as default.

##### `saveLanguage(languageCode)`
Save language preference to localStorage.

##### `updateUI()`
Update all elements with `data-i18n` attributes to the current language.

##### `on(event, callback)`
Register an event listener.
- `event`: Event name (currently only `'languageChanged'`)
- `callback`: Function to execute when event fires

##### `setTranslations(translations)`
Update the translations object and refresh UI.

### Translation Structure

Translations should be organized by language code:

```javascript
const translations = {
    en: {
        'page.title': 'Page Title',
        'action.save': 'Save',
        'placeholder.search': 'Search...'
    },
    uz: {
        'page.title': 'Sahifa Sarlavhasi',
        'action.save': 'Saqlash',
        'placeholder.search': 'Qidirish...'
    },
    ru: {
        'page.title': 'Заголовок Страницы',
        'action.save': 'Сохранить',
        'placeholder.search': 'Поиск...'
    }
};
```

### Requirements Satisfied
- **2.1**: Language selector in UI header
- **2.2**: Update UI within 200ms
- **2.3**: Persist language preference to localStorage
- **2.4**: Display content in previously selected language on return
- **2.6**: Fallback to English for missing translations

### Testing

A test page is available at `/static/admin/test-language-switcher.html` that demonstrates:
- Language switching functionality
- UI text updates
- localStorage persistence
- Performance tracking
- Event system

### Browser Support
- Modern browsers with ES6 support
- localStorage API required for persistence
- Performance API used for timing measurements

### Notes
- The component uses the `preferred_language` key in localStorage
- Performance warnings are logged if UI updates exceed 200ms
- Missing translations automatically fall back to English
- The component is framework-agnostic (vanilla JavaScript)


---

## EnhancedTable Component

### Overview
The EnhancedTable component provides a professional, interactive table display with sorting, bulk selection, and row actions. It's designed for displaying entity lists (subjects, levels, tests, questions) with a rich user experience.

### Features
- **Sortable Columns**: Click column headers to sort ascending/descending
- **Visual Sort Indicators**: Shows arrows (↑ ↓) for current sort state
- **Zebra Striping**: Alternating row colors for improved readability
- **Row Hover**: Highlights rows on mouse hover
- **Bulk Selection**: Checkboxes for selecting multiple rows
- **Select All**: Master checkbox to select/deselect all rows
- **Selected Count**: Displays count of selected items
- **Row Actions**: Edit and delete buttons for each row
- **Event System**: Emits events for all user actions
- **Empty State**: Displays friendly message when no data
- **Custom Rendering**: Support for custom column render functions
- **Responsive Design**: Works with Tailwind CSS utilities

### Usage

#### Basic Setup
```javascript
// Define columns
const columns = [
    { key: 'name', label: 'Name', sortable: true },
    { key: 'level', label: 'Level', sortable: true },
    { key: 'tests', label: 'Tests', sortable: true }
];

// Initialize table
const table = new EnhancedTable('table-container', columns, {
    selectable: true,
    actions: true,
    emptyMessage: 'No data available'
});

// Set data
table.setData(dataArray);
```

#### HTML Integration
```html
<!-- Container for the table -->
<div id="table-container"></div>
```

#### Column Definitions

Columns are defined as objects with the following properties:

```javascript
{
    key: 'fieldName',        // Data field name (required)
    label: 'Column Header',  // Display label (required)
    sortable: true,          // Enable sorting (default: true)
    render: (value, row) => {  // Custom render function (optional)
        return `<span class="font-bold">${value}</span>`;
    }
}
```

#### Custom Render Functions

Use render functions to format cell values:

```javascript
const columns = [
    {
        key: 'price',
        label: 'Price',
        sortable: true,
        render: (value) => {
            if (value === 0) {
                return '<span class="text-green-600">Free</span>';
            }
            return `$${value.toFixed(2)}`;
        }
    },
    {
        key: 'created',
        label: 'Created',
        sortable: true,
        render: (value) => {
            return new Date(value).toLocaleDateString();
        }
    }
];
```

#### Event Handling

Listen to table events:

```javascript
// Row edit event
table.on('rowEdit', (data) => {
    console.log('Edit row:', data.id, data.row);
    // Open edit form
});

// Row delete event
table.on('rowDelete', (data) => {
    console.log('Delete row:', data.id, data.row);
    // Show confirmation dialog
});

// Selection change event
table.on('rowSelect', (data) => {
    console.log('Selected:', data.selectedIds);
    console.log('Selected rows:', data.selectedRows);
    // Update bulk action toolbar
});

// Sort change event
table.on('sortChange', (data) => {
    console.log('Sorted by:', data.column, data.direction);
    // Update URL or state
});
```

#### API Methods

##### `constructor(containerId, columns, options)`
Initialize the enhanced table.
- `containerId`: ID of the container element
- `columns`: Array of column definition objects
- `options`: Configuration object
  - `selectable`: Enable bulk selection (default: false)
  - `actions`: Show row actions (default: true)
  - `emptyMessage`: Message when no data (default: "No data available")
  - `idField`: Field name for row ID (default: "id")

##### `setData(data)`
Set table data and render.
- `data`: Array of data objects

##### `sort(columnKey, direction)`
Sort table by column.
- `columnKey`: Column key to sort by
- `direction`: Sort direction ('asc' or 'desc', optional)

##### `getSelectedRows()`
Get array of selected row objects.

##### `clearSelection()`
Clear all row selections.

##### `on(event, callback)`
Register an event listener.
- `event`: Event name ('rowEdit', 'rowDelete', 'rowSelect', 'sortChange')
- `callback`: Function to execute when event fires

### Sorting Behavior

The table automatically detects data types and sorts accordingly:
- **Numbers**: Numeric comparison
- **Dates**: Date comparison (ISO format or Date objects)
- **Strings**: Alphabetical comparison (case-insensitive)
- **Null/Undefined**: Always sorted to the end

Click a column header once for ascending sort, click again for descending sort.

### Selection Behavior

When `selectable: true`:
- Checkboxes appear in the first column
- "Select All" checkbox appears in the header
- Selected count is displayed above the table
- Selected rows are highlighted with blue background
- `rowSelect` event fires on selection changes

### Row Actions

When `actions: true`:
- Edit and delete buttons appear in the last column
- Edit button (blue) emits `rowEdit` event
- Delete button (red) emits `rowDelete` event
- Buttons show icons and have hover effects

### Styling

The component uses Tailwind CSS classes for styling:
- Zebra striping: Alternating white and gray backgrounds
- Hover effect: Blue highlight on row hover
- Sort indicators: Up/down arrows in column headers
- Action buttons: Icon buttons with color-coded hover states
- Empty state: Centered message with icon

### Requirements Satisfied
- **10.1**: Display entity lists in tables with clear column headers
- **10.2**: Make table columns sortable by clicking header
- **10.3**: Sort table in ascending order on first click
- **10.4**: Reverse sort order on second click
- **10.5**: Display visual indicator for sort column and direction
- **10.6**: Apply zebra striping to table rows
- **10.7**: Highlight table rows on hover
- **10.8**: Display row actions consistently
- **15.1**: Display checkboxes for selecting multiple items
- **15.2**: Display "Select All" checkbox in header
- **15.3**: Select all visible items when "Select All" is checked
- **15.5**: Display count of selected items

### Demo

A demo page is available at `enhanced-table-demo.html` that demonstrates:
- Sortable columns with multiple data types
- Bulk selection with "Select All"
- Row actions (edit and delete)
- Custom render functions
- Event system
- Empty state
- Dynamic data manipulation

### Browser Support
- Modern browsers with ES6 support
- Tailwind CSS required for styling
- No external dependencies

### Notes
- The component is framework-agnostic (vanilla JavaScript)
- Data is sorted in-place (modifies the data array)
- Selection state is maintained across re-renders
- Custom render functions receive both value and full row object
- The component handles keyboard accessibility for sortable headers


---

## ConfirmationDialog Component

### Overview
The ConfirmationDialog component displays modal confirmation dialogs for destructive actions. It provides clear messaging, cascade deletion warnings, and keyboard accessibility to prevent accidental data loss.

### Features
- **Modal Overlay**: Semi-transparent dark background with centered dialog
- **Multiple Types**: Delete, warning, and info dialog styles
- **Cascade Warnings**: Special warning section for cascade deletions
- **Keyboard Support**: Escape key to cancel, Tab for focus navigation
- **Focus Management**: Traps focus within dialog, restores on close
- **Accessibility**: ARIA attributes, keyboard navigation, focus indicators
- **Event System**: Emits confirm and cancel events
- **Customizable**: Configurable title, message, button text, and type
- **Visual Feedback**: Color-coded icons and buttons based on action type

### Usage

#### Basic Delete Confirmation
```javascript
const dialog = new ConfirmationDialog({
    title: 'Delete Item',
    message: 'Are you sure you want to delete this item? This action cannot be undone.',
    confirmText: 'Delete',
    cancelText: 'Cancel',
    type: 'delete'
});

dialog.on('confirm', () => {
    // Perform delete operation
    deleteItem(itemId);
});

dialog.on('cancel', () => {
    // User cancelled, do nothing
    console.log('Delete cancelled');
});

dialog.show();
```

#### Delete with Cascade Warning
```javascript
const dialog = new ConfirmationDialog({
    title: 'Delete Subject',
    message: 'Are you sure you want to delete "Mathematics"?',
    confirmText: 'Delete Subject',
    cancelText: 'Cancel',
    type: 'delete',
    cascadeWarning: 'Warning: Deleting this subject will also delete all its levels, tests, and questions. This action cannot be undone.'
});

dialog.on('confirm', () => {
    deleteSubject(subjectId);
});

dialog.show();
```

#### Warning Dialog
```javascript
const dialog = new ConfirmationDialog({
    title: 'Unsaved Changes',
    message: 'You have unsaved changes. Are you sure you want to leave this page?',
    confirmText: 'Leave Page',
    cancelText: 'Stay',
    type: 'warning'
});

dialog.on('confirm', () => {
    window.location.href = '/other-page';
});

dialog.show();
```

#### Info Dialog
```javascript
const dialog = new ConfirmationDialog({
    title: 'Export Data',
    message: 'This will export all subjects and their related data to a CSV file. Continue?',
    confirmText: 'Export',
    cancelText: 'Cancel',
    type: 'info'
});

dialog.on('confirm', () => {
    exportData();
});

dialog.show();
```

#### Bulk Delete Confirmation
```javascript
const selectedCount = 5;
const dialog = new ConfirmationDialog({
    title: 'Delete Multiple Items',
    message: `Are you sure you want to delete ${selectedCount} selected items?`,
    confirmText: 'Delete All',
    cancelText: 'Cancel',
    type: 'delete',
    cascadeWarning: 'Note: Some items may have related data that will also be deleted.'
});

dialog.on('confirm', () => {
    bulkDeleteItems(selectedIds);
});

dialog.show();
```

### Constructor Options

```javascript
new ConfirmationDialog({
    title: 'Confirm Action',           // Dialog title (default: "Confirm Action")
    message: 'Are you sure?',          // Main message (default: "Are you sure you want to proceed?")
    confirmText: 'Confirm',            // Confirm button text (default: "Confirm")
    cancelText: 'Cancel',              // Cancel button text (default: "Cancel")
    type: 'delete',                    // Dialog type: 'delete', 'warning', 'info' (default: 'warning')
    cascadeWarning: 'Warning text...'  // Optional cascade warning message (default: null)
});
```

### Dialog Types

#### Delete Type (`type: 'delete'`)
- **Icon**: Red trash can icon
- **Button**: Red confirm button
- **Use for**: Permanent deletion actions

#### Warning Type (`type: 'warning'`)
- **Icon**: Yellow warning triangle
- **Button**: Yellow confirm button
- **Use for**: Potentially dangerous actions, unsaved changes

#### Info Type (`type: 'info'`)
- **Icon**: Blue information icon
- **Button**: Blue confirm button
- **Use for**: Informational confirmations, exports, non-destructive actions

### API Methods

##### `constructor(options)`
Initialize the confirmation dialog.
- `options`: Configuration object (see Constructor Options above)

##### `show()`
Display the confirmation dialog. Automatically:
- Stores currently focused element
- Renders and adds dialog to DOM
- Sets up event listeners
- Focuses the confirm button
- Traps focus within dialog

##### `hide()`
Hide the confirmation dialog. Automatically:
- Restores focus to previous element
- Removes dialog from DOM
- Cleans up event listeners

##### `setMessage(message)`
Update the dialog message.
- `message`: New message text

##### `setCascadeWarning(warning)`
Update the cascade warning message.
- `warning`: New warning text

##### `on(event, callback)`
Register an event listener.
- `event`: Event name ('confirm' or 'cancel')
- `callback`: Function to execute when event fires

### Event System

The component emits two events:

#### `confirm` Event
Fired when user clicks the confirm button.

```javascript
dialog.on('confirm', () => {
    // User confirmed the action
    performAction();
});
```

#### `cancel` Event
Fired when user:
- Clicks the cancel button
- Clicks outside the dialog (on overlay)
- Presses the Escape key

```javascript
dialog.on('cancel', () => {
    // User cancelled the action
    console.log('Action cancelled');
});
```

### Keyboard Accessibility

The dialog supports full keyboard navigation:

- **Escape**: Close dialog (triggers cancel event)
- **Tab**: Navigate between buttons
- **Shift+Tab**: Navigate backwards
- **Enter/Space**: Activate focused button
- **Focus Trap**: Focus stays within dialog until closed

### Accessibility Features

- **ARIA Attributes**: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `aria-describedby`
- **Focus Management**: Automatically focuses confirm button on open, restores previous focus on close
- **Focus Trap**: Prevents focus from leaving dialog while open
- **Keyboard Support**: Full keyboard navigation and control
- **Screen Reader Support**: Proper labeling and structure for assistive technologies

### Cascade Warning Display

When `cascadeWarning` is provided, a special warning section appears:
- Yellow background with border
- Warning icon
- Prominent warning text
- Positioned between message and buttons

Example cascade warnings:
- "Deleting this subject will also delete all its levels and tests"
- "Deleting this level will also delete all its tests and questions"
- "Some items may have related data that will also be deleted"

### Styling

The component uses Tailwind CSS classes:
- **Overlay**: Fixed full-screen with semi-transparent black background
- **Dialog**: White rounded card with shadow, max-width 28rem
- **Icons**: Color-coded based on type (red, yellow, blue)
- **Buttons**: Color-coded with hover effects and focus rings
- **Cascade Warning**: Yellow background with warning icon

### Requirements Satisfied
- **13.1**: Display confirmation dialog before delete operations
- **13.2**: Clearly state what will be deleted
- **13.3**: Warn about cascade deletions
- **13.4**: Provide "Confirm" and "Cancel" buttons
- **13.5**: Close dialog without deleting on "Cancel"

### Demo

A demo page is available at `confirmation-dialog-demo.html` that demonstrates:
- Delete confirmation with red button
- Delete with cascade warning
- Warning dialog with yellow button
- Info dialog with blue button
- Bulk delete confirmation
- Event logging
- Keyboard shortcuts

### Browser Support
- Modern browsers with ES6 support
- Tailwind CSS required for styling
- No external dependencies

### Notes
- The component is framework-agnostic (vanilla JavaScript)
- Dialog is automatically removed from DOM when hidden
- Multiple dialogs can be created but only one should be shown at a time
- XSS protection: All text content is escaped before rendering
- Focus is properly managed for accessibility
- The component handles cleanup of event listeners automatically


---

## Notification Component

### Overview
The Notification component displays toast-style notifications for user feedback. It supports multiple notification types with auto-dismiss and manual dismiss options, providing clear visual feedback for operations.

### Features
- **Toast-Style**: Notifications appear in top-right corner
- **Multiple Types**: Success (green), error (red), warning (yellow), info (blue)
- **Auto-Dismiss**: Success notifications auto-dismiss after 3 seconds
- **Manual Dismiss**: Error notifications require manual dismiss
- **Stacking**: Multiple notifications stack vertically
- **Smooth Animations**: Slide-in and slide-out transitions
- **Accessibility**: ARIA attributes for screen readers
- **Singleton Pattern**: One notification manager instance
- **Event-Driven**: Non-blocking user feedback
- **Customizable**: Configurable duration and dismissibility

### Usage

#### Basic Notifications
```javascript
// Success notification (auto-dismisses after 3 seconds)
notificationManager.success('Changes saved successfully!');

// Error notification (manual dismiss required)
notificationManager.error('An error occurred. Please try again.');

// Warning notification
notificationManager.warning('This action cannot be undone.');

// Info notification
notificationManager.info('New updates are available.');
```

#### Custom Duration
```javascript
// Auto-dismiss after 5 seconds
notificationManager.success('Operation completed!', { duration: 5000 });

// No auto-dismiss (manual dismiss only)
notificationManager.warning('Important message', { duration: 0 });

// Quick notification (1 second)
notificationManager.info('Copied to clipboard', { duration: 1000 });
```

#### Advanced Usage
```javascript
// Show notification with custom options
const id = notificationManager.show('Custom message', 'success', {
    duration: 4000,
    dismissible: true
});

// Manually dismiss a specific notification
notificationManager.dismiss(id);

// Dismiss all notifications
notificationManager.dismissAll();
```

#### Real-World Examples

##### Form Submission Success
```javascript
async function saveForm() {
    try {
        await api.saveData(formData);
        notificationManager.success('Form submitted successfully!');
    } catch (error) {
        notificationManager.error('Failed to submit form. Please try again.');
    }
}
```

##### Validation Errors
```javascript
function validateForm() {
    const errors = [];
    
    if (!name) errors.push('Name is required');
    if (!email) errors.push('Email is required');
    
    if (errors.length > 0) {
        notificationManager.error(errors.join('. '));
        return false;
    }
    
    return true;
}
```

##### Delete Confirmation
```javascript
async function deleteItem(id) {
    try {
        await api.deleteItem(id);
        notificationManager.success('Item deleted successfully!');
        reloadList();
    } catch (error) {
        notificationManager.error('Failed to delete item. It may be in use.');
    }
}
```

##### Multi-Step Process
```javascript
async function processData() {
    notificationManager.info('Processing data...');
    
    try {
        await step1();
        notificationManager.success('Step 1 complete');
        
        await step2();
        notificationManager.success('Step 2 complete');
        
        await step3();
        notificationManager.success('All steps completed!');
    } catch (error) {
        notificationManager.error('Process failed: ' + error.message);
    }
}
```

### API Methods

##### `show(message, type, options)`
Show a notification with full control.
- `message`: Message text to display (required)
- `type`: Notification type: 'success', 'error', 'warning', 'info' (default: 'info')
- `options`: Configuration object
  - `duration`: Auto-dismiss duration in milliseconds (0 = no auto-dismiss)
  - `dismissible`: Whether notification can be manually dismissed (default: true)
- Returns: Notification ID (number)

##### `success(message, options)`
Show a success notification (green, auto-dismisses after 3 seconds).
- `message`: Message text to display
- `options`: Optional configuration object
- Returns: Notification ID

##### `error(message, options)`
Show an error notification (red, manual dismiss required).
- `message`: Message text to display
- `options`: Optional configuration object
- Returns: Notification ID

##### `warning(message, options)`
Show a warning notification (yellow, auto-dismisses after 5 seconds).
- `message`: Message text to display
- `options`: Optional configuration object
- Returns: Notification ID

##### `info(message, options)`
Show an info notification (blue, auto-dismisses after 4 seconds).
- `message`: Message text to display
- `options`: Optional configuration object
- Returns: Notification ID

##### `dismiss(id)`
Manually dismiss a specific notification.
- `id`: Notification ID returned from show/success/error/warning/info

##### `dismissAll()`
Dismiss all active notifications.

### Notification Types

#### Success (`success`)
- **Color**: Green
- **Icon**: Checkmark in circle
- **Default Duration**: 3000ms (3 seconds)
- **Use for**: Successful operations, confirmations

#### Error (`error`)
- **Color**: Red
- **Icon**: X in circle
- **Default Duration**: 0 (no auto-dismiss)
- **Use for**: Errors, failures, validation issues

#### Warning (`warning`)
- **Color**: Yellow
- **Icon**: Warning triangle
- **Default Duration**: 5000ms (5 seconds)
- **Use for**: Warnings, cautions, important notices

#### Info (`info`)
- **Color**: Blue
- **Icon**: Information circle
- **Default Duration**: 4000ms (4 seconds)
- **Use for**: General information, tips, updates

### Default Behavior

Each notification type has sensible defaults:

```javascript
// Success: Auto-dismiss after 3 seconds, dismissible
notificationManager.success('Saved!');
// Equivalent to:
notificationManager.show('Saved!', 'success', { duration: 3000, dismissible: true });

// Error: No auto-dismiss, dismissible (manual dismiss required)
notificationManager.error('Failed!');
// Equivalent to:
notificationManager.show('Failed!', 'error', { duration: 0, dismissible: true });
```

### Stacking Behavior

Multiple notifications stack vertically:
- New notifications appear at the top
- Older notifications move down
- Maximum width: 28rem (448px)
- Gap between notifications: 0.75rem (12px)
- Positioned in top-right corner with 1rem (16px) margin

### Animation

Notifications use smooth CSS transitions:
- **Slide-in**: Slides from right with fade-in (300ms)
- **Slide-out**: Slides to right with fade-out (300ms)
- **Auto-dismiss**: Waits for duration, then slides out

### Accessibility

- **ARIA Live Regions**: Notifications use `aria-live="polite"` (or `assertive` for errors)
- **ARIA Atomic**: Set to `false` to announce only new notifications
- **Dismiss Button**: Labeled with `aria-label="Dismiss notification"`
- **Keyboard Support**: Dismiss button is keyboard accessible
- **Screen Reader**: Announces notification message when shown

### Styling

The component uses Tailwind CSS classes:
- **Container**: Fixed position in top-right corner
- **Notification**: White background with colored left border
- **Icons**: Color-coded circular backgrounds
- **Dismiss Button**: Gray with hover effect
- **Shadow**: Large shadow for depth
- **Border**: 4px left border in notification color

### Requirements Satisfied
- **12.4**: Display success notifications after successful operations
- **12.5**: Display error notifications when operations fail
- **12.6**: Auto-dismiss success notifications after 3 seconds
- **12.7**: Keep error notifications visible until dismissed by user

### Demo

A demo page is available at `notification-demo.html` that demonstrates:
- All notification types (success, error, warning, info)
- Custom duration options
- Multiple stacked notifications
- Dismiss all functionality
- Real-world usage examples
- Auto-dismiss vs manual dismiss behavior

### Browser Support
- Modern browsers with ES6 support
- Tailwind CSS required for styling
- No external dependencies

### Notes
- The component is a singleton (only one instance exists)
- Access via global `notificationManager` variable
- Notifications are automatically removed from DOM after dismissal
- The component is framework-agnostic (vanilla JavaScript)
- XSS protection: Message text is properly escaped
- Smooth animations use CSS transitions


---

## LoadingSpinner Component

### Overview
The LoadingSpinner component provides visual feedback during asynchronous operations. It supports multiple loading states including skeleton screens, button spinners, and full-page overlays.

### Features
- **Skeleton Screens**: Animated placeholders for initial page load
- **Button Spinners**: Loading indicators on submit buttons
- **Full-Page Overlay**: Semi-transparent overlay for long operations
- **Multiple Skeleton Types**: List, card, and form layouts
- **Accessibility**: ARIA attributes for screen readers
- **Non-Blocking**: Provides feedback without blocking UI
- **Smooth Animations**: Pulse and spin animations
- **Singleton Pattern**: One loading manager instance
- **State Management**: Tracks active loading states

### Usage

#### Skeleton Screens

##### List Skeleton
```javascript
// Show skeleton for list view
loadingSpinner.showSkeleton('content-container', {
    type: 'list',
    rows: 5
});

// Load data
const data = await fetchData();

// Hide skeleton and show data
loadingSpinner.hideSkeleton('content-container');
renderData(data);
```

##### Card Skeleton
```javascript
// Show skeleton for card grid
loadingSpinner.showSkeleton('card-grid', {
    type: 'card',
    rows: 6
});

// Load data
const items = await fetchItems();

// Hide skeleton and show cards
loadingSpinner.hideSkeleton('card-grid');
renderCards(items);
```

##### Form Skeleton
```javascript
// Show skeleton for form
loadingSpinner.showSkeleton('form-container', {
    type: 'form',
    rows: 4
});

// Load form data
const formData = await fetchFormData();

// Hide skeleton and show form
loadingSpinner.hideSkeleton('form-container');
renderForm(formData);
```

#### Button Spinners

##### Form Submit
```javascript
async function submitForm() {
    // Show spinner on button
    loadingSpinner.showButtonSpinner('submit-button', {
        text: 'Submitting...'
    });
    
    try {
        await api.submitForm(formData);
        notificationManager.success('Form submitted!');
    } catch (error) {
        notificationManager.error('Submission failed');
    } finally {
        // Hide spinner
        loadingSpinner.hideButtonSpinner('submit-button');
    }
}
```

##### Delete Action
```javascript
async function deleteItem(id) {
    loadingSpinner.showButtonSpinner('delete-button', {
        text: 'Deleting...'
    });
    
    try {
        await api.deleteItem(id);
        notificationManager.success('Item deleted!');
    } finally {
        loadingSpinner.hideButtonSpinner('delete-button');
    }
}
```

##### Save Action
```javascript
async function saveChanges() {
    loadingSpinner.showButtonSpinner('save-button', {
        text: 'Saving...'
    });
    
    try {
        await api.saveChanges(data);
        notificationManager.success('Changes saved!');
    } finally {
        loadingSpinner.hideButtonSpinner('save-button');
    }
}
```

#### Full-Page Overlay

##### Long Operation
```javascript
async function processLargeFile() {
    // Show overlay
    loadingSpinner.showOverlay({
        message: 'Processing file...'
    });
    
    try {
        await api.processFile(file);
        notificationManager.success('File processed!');
    } finally {
        // Hide overlay
        loadingSpinner.hideOverlay();
    }
}
```

##### Bulk Operation
```javascript
async function bulkDelete(ids) {
    loadingSpinner.showOverlay({
        message: `Deleting ${ids.length} items...`
    });
    
    try {
        await api.bulkDelete(ids);
        notificationManager.success('Items deleted!');
        reloadList();
    } finally {
        loadingSpinner.hideOverlay();
    }
}
```

##### File Upload
```javascript
async function uploadFiles(files) {
    loadingSpinner.showOverlay({
        message: 'Uploading files...'
    });
    
    try {
        await api.uploadFiles(files);
        notificationManager.success('Files uploaded!');
    } finally {
        loadingSpinner.hideOverlay();
    }
}
```

### API Methods

##### `showSkeleton(containerId, options)`
Show skeleton screen in a container.
- `containerId`: ID of container element (required)
- `options`: Configuration object
  - `rows`: Number of skeleton rows (default: 3)
  - `type`: Skeleton type: 'list', 'card', 'form' (default: 'list')

##### `hideSkeleton(containerId)`
Hide skeleton screen and restore original content.
- `containerId`: ID of container element (required)

##### `showButtonSpinner(buttonId, options)`
Show spinner on a button.
- `buttonId`: ID of button element (required)
- `options`: Configuration object
  - `text`: Loading text to display (default: 'Loading...')

##### `hideButtonSpinner(buttonId)`
Hide spinner from button and restore original state.
- `buttonId`: ID of button element (required)

##### `showOverlay(options)`
Show full-page loading overlay.
- `options`: Configuration object
  - `message`: Loading message to display (default: 'Loading...')

##### `hideOverlay()`
Hide full-page loading overlay.

### Skeleton Types

#### List Skeleton (`type: 'list'`)
Displays rows with:
- Circular avatar placeholder (left)
- Two text line placeholders (right)
- White background with border
- Suitable for: Entity lists, search results, feeds

#### Card Skeleton (`type: 'card'`)
Displays cards with:
- Large rectangular image placeholder (top)
- Two text line placeholders (bottom)
- Grid layout (responsive)
- Suitable for: Product grids, image galleries, dashboards

#### Form Skeleton (`type: 'form'`)
Displays form fields with:
- Small label placeholder (top)
- Large input placeholder (bottom)
- Vertical stacking
- Suitable for: Forms, settings pages, edit views

### Button Spinner Behavior

When `showButtonSpinner` is called:
1. Button is disabled (prevents double-submission)
2. Original content is stored
3. Spinner icon and text are displayed
4. `aria-busy="true"` is set

When `hideButtonSpinner` is called:
1. Original content is restored
2. Original disabled state is restored
3. `aria-busy` is removed

### Overlay Behavior

The overlay:
- Covers entire viewport
- Semi-transparent black background (50% opacity)
- Centers spinner and message
- Prevents interaction with page
- Fades in/out smoothly (300ms)
- Can be dismissed by calling `hideOverlay()`

### Animations

#### Pulse Animation (Skeleton)
- Opacity oscillates between 100% and 50%
- Duration: 2 seconds
- Easing: cubic-bezier(0.4, 0, 0.6, 1)
- Infinite loop

#### Spin Animation (Spinner)
- Rotates 360 degrees
- Duration: 1 second
- Easing: linear
- Infinite loop

### Accessibility

- **ARIA Busy**: `aria-busy="true"` set on loading elements
- **ARIA Live**: `aria-live="polite"` for skeleton containers
- **ARIA Alert**: `aria-live="assertive"` for overlay
- **Role**: `role="alert"` for overlay
- **Screen Reader**: Announces loading state changes

### State Management

The component tracks:
- **Active Skeletons**: Map of container IDs to original content
- **Active Buttons**: Map of button IDs to original state
- **Overlay**: Reference to current overlay element

This allows:
- Multiple skeletons in different containers
- Multiple button spinners simultaneously
- Proper cleanup and restoration

### Styling

The component uses Tailwind CSS classes:
- **Skeleton**: Gray backgrounds with pulse animation
- **Spinner**: Circular SVG with spin animation
- **Overlay**: Fixed full-screen with backdrop
- **Button Spinner**: Inline flex with gap

### Requirements Satisfied
- **12.1**: Display skeleton screens during data loading
- **12.2**: Display spinner on submit buttons during processing
- **12.3**: Display progress indicator for bulk operations

### Demo

A demo page is available at `loading-spinner-demo.html` that demonstrates:
- All skeleton types (list, card, form)
- Button spinners with different text
- Full-page overlay with custom messages
- Real-world scenarios (page load, form submit, bulk operation)
- State management and cleanup

### Browser Support
- Modern browsers with ES6 support
- Tailwind CSS required for styling
- No external dependencies

### Notes
- The component is a singleton (only one instance exists)
- Access via global `loadingSpinner` variable
- Original content is preserved and restored
- Multiple skeletons can be active simultaneously
- Multiple button spinners can be active simultaneously
- Only one overlay can be active at a time
- The component is framework-agnostic (vanilla JavaScript)
- Smooth animations use CSS transitions and keyframes
