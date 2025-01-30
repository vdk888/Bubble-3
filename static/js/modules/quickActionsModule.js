export class QuickActionsModule {
    constructor(chatModule) {
        this.chatModule = chatModule;
        this.actionHandlers = {
            'portfolio-overview': () => this.chatModule.sendMessage('portfolio-overview'),
            'portfolio-performance': () => this.chatModule.sendMessage('portfolio-performance'),
            'market-overview': () => this.chatModule.sendMessage('market-overview'),
            'market-news': () => this.chatModule.sendMessage('market-news'),
            'risk-analysis': () => this.chatModule.sendMessage('risk-analysis'),
            'technical-indicators': () => this.chatModule.sendMessage('technical-indicators'),
            'start-guide': () => this.chatModule.sendMessage('start-guide')
        };
    }

    initialize() {
        // Set up event listeners for quick action buttons
        document.querySelectorAll('.action-btn').forEach(button => {
            const action = button.dataset.action;
            if (this.actionHandlers[action]) {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Quick action clicked:', action); // Debug log
                    this.actionHandlers[action]();
                    // Hide the sub-actions after clicking
                    const subActions = button.closest('.sub-actions');
                    if (subActions) {
                        subActions.style.display = 'none';
                    }
                });
            }
        });

        // Set up event listeners for category buttons
        document.querySelectorAll('.category-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const category = button.closest('.action-category');
                if (category) {
                    // Toggle sub-actions visibility
                    const subActions = category.querySelector('.sub-actions');
                    if (subActions) {
                        const isVisible = subActions.style.display === 'flex';
                        // Hide all other sub-actions first
                        document.querySelectorAll('.sub-actions').forEach(sa => {
                            sa.style.display = 'none';
                        });
                        // Toggle this one
                        subActions.style.display = isVisible ? 'none' : 'flex';
                    }
                    
                    // If this is the guide button, handle it directly
                    if (category.classList.contains('guide')) {
                        this.actionHandlers['start-guide']();
                    }
                }
            });
        });

        // Close sub-actions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.action-category')) {
                document.querySelectorAll('.sub-actions').forEach(sa => {
                    sa.style.display = 'none';
                });
            }
        });
    }
} 