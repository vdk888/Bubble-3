// Portfolio Module
import { formatCurrency, formatPercentage } from './uiModule.js';

export class PortfolioModule {
    constructor() {
        this.updateInterval = null;
        this.accountSummary = document.getElementById('account-summary');
    }

    initialize() {
        // Listen for credentials stored event
        document.addEventListener('credentialsStored', (event) => {
            this.updateDashboardMetrics(event.detail);
        });

        // Initial portfolio data load
        this.updatePortfolioData();
    }

    async updatePortfolioData() {
        try {
            console.log('Fetching portfolio metrics...');
            const response = await fetch('/api/portfolio/metrics');
            const data = await response.json();
            
            console.log('Raw API response:', data);
            
            if (data.error) {
                console.error('API returned error:', data.error);
                this.accountSummary.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }

            if (data.metrics) {
                this.updateDashboardMetrics(data.metrics);
            } else {
                console.error('No metrics data in response');
            }
        } catch (error) {
            console.error('Error updating portfolio:', error);
            this.accountSummary.innerHTML = '<div class="error-message">Error loading portfolio data. Please check your Alpaca credentials.</div>';
        }
    }

    updateDashboardMetrics(metrics) {
        console.log('Updating dashboard with metrics:', metrics);
        
        try {
            // Remove error message if it exists
            if (this.accountSummary) {
                const errorMessage = this.accountSummary.querySelector('.error-message');
                if (errorMessage) {
                    errorMessage.remove();
                }
            }

            // Update metric values
            const elements = {
                'buying-power': metrics['Buying Power'],
                'cash-available': metrics['Cash Available'],
                'daily-change': metrics['Daily Change'],
                'total-value': metrics['Total Value']
            };

            for (const [id, value] of Object.entries(elements)) {
                const element = document.getElementById(id);
                if (element) {
                    const formattedValue = id.includes('change') ? 
                        formatPercentage(parseFloat(value)) : 
                        formatCurrency(parseFloat(value));
                    element.textContent = formattedValue;
                }
            }

            // Start regular updates
            this.startPeriodicUpdates();
        } catch (error) {
            console.error('Error updating dashboard metrics:', error);
        }
    }

    startPeriodicUpdates() {
        // Clear any existing interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Set up new interval
        this.updateInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/portfolio/metrics');
                const data = await response.json();
                if (data.metrics) {
                    this.updateDashboardMetrics(data.metrics);
                }
            } catch (error) {
                console.error('Error in periodic update:', error);
            }
        }, 30000);
    }

    stopPeriodicUpdates() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
} 