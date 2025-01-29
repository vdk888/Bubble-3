// UI Module

// Format currency values
export function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// Format percentage values
export function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value / 100);
}

// Get chart colors
export function getChartColor(index) {
    const colors = [
        '#4CAF50', // Green
        '#2196F3', // Blue
        '#FFC107', // Yellow
        '#9C27B0', // Purple
        '#FF5722', // Deep Orange
        '#00BCD4', // Cyan
        '#795548', // Brown
        '#9E9E9E'  // Grey
    ];
    return colors[index % colors.length];
}

// Initialize UI elements
export function initializeUIElements() {
    const toolButtons = document.querySelectorAll('.tool-button');
    const actionButtons = document.querySelectorAll('.action-btn');

    // Initialize tool buttons
    if (toolButtons) {
        toolButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tool = this.dataset.tool;
                // Emit toolSelected event
                const event = new CustomEvent('toolSelected', { detail: tool });
                document.dispatchEvent(event);
            });
        });
    }

    // Initialize action buttons
    if (actionButtons) {
        actionButtons.forEach(button => {
            button.addEventListener('click', function() {
                const action = this.dataset.action;
                // Emit actionSelected event
                const event = new CustomEvent('actionSelected', { detail: action });
                document.dispatchEvent(event);
            });
        });
    }
} 