// Main Dashboard Script
import { ChatModule } from './modules/chatModule.js';
import { PortfolioModule } from './modules/portfolioModule.js';
import { ToolsModule } from './modules/toolsModule.js';
import { ChartModule } from './modules/chartModule.js';
import { initializeUIElements } from './modules/uiModule.js';

class Dashboard {
    constructor() {
        this.chatModule = new ChatModule();
        this.portfolioModule = new PortfolioModule();
        this.toolsModule = new ToolsModule();
        this.chartModule = new ChartModule();
    }

    initialize() {
        // Initialize UI elements
        initializeUIElements();

        // Initialize all modules
        this.chatModule.initialize();
        this.portfolioModule.initialize();

        // Show initial greeting
        this.chatModule.showInitialGreeting();

        // Setup event listeners for action buttons
        document.addEventListener('actionSelected', (event) => {
            if (this.chatModule.messageInput) {
                this.chatModule.messageInput.value = event.detail;
                this.chatModule.processMessage(event.detail);
            }
        });

        // Handle window unload
        window.addEventListener('beforeunload', () => {
            this.portfolioModule.stopPeriodicUpdates();
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.initialize();
}); 