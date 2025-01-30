export class QuickActionsModule {
    constructor(chatModule) {
        this.chatModule = chatModule;
        this.actionHandlers = {
            'portfolio-overview': () => this.handleAction('Can you give me an overview of my current portfolio?'),
            'portfolio-performance': () => this.handleAction('Analyze my portfolio performance'),
            'market-overview': () => this.handleAction('What\'s happening in the markets today? Give me a summary of major indices.'),
            'market-news': () => this.handleAction('What are the latest market news and developments?'),
            'risk-analysis': () => this.handleAction('Can you analyze the risk level of my current portfolio?'),
            'technical-indicators': () => this.handleAction('Show me the key technical indicators for my portfolio holdings'),
            'start-guide': () => this.handleAction('I\'m new here. Can you guide me through what you can help me with?')
        };
    }

    handleAction(message) {
        console.log('Sending action message:', message);
        this.chatModule.sendMessage(message);
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