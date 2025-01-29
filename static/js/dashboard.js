// Main Dashboard Script
import { ChatModule } from './modules/chatModule.js';
import { PortfolioModule } from './modules/portfolioModule.js';
import { ToolsModule } from './modules/toolsModule.js';
import { ChartModule } from './modules/chartModule.js';
import { PerformanceModule } from './modules/performanceModule.js';
import { initializeUIElements } from './modules/uiModule.js';

class Dashboard {
    constructor() {
        this.chatModule = new ChatModule();
        this.portfolioModule = new PortfolioModule();
        this.toolsModule = new ToolsModule();
        this.chartModule = new ChartModule();
        this.performanceModule = new PerformanceModule();
    }

    initialize() {
        // Initialize UI elements
        initializeUIElements();

        // Initialize all modules
        this.chatModule.initialize();  // This will handle the greeting internally
        this.portfolioModule.initialize();

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

        // Listen for credentials stored event to show performance
        document.addEventListener('credentialsStored', () => {
            const performanceSection = document.getElementById('performance-section');
            if (performanceSection) {
                performanceSection.style.display = 'block';
                this.performanceModule.loadPerformanceData('1D');
            }
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new Dashboard();
    dashboard.initialize();
}); 