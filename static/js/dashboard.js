class DashboardInterface {
    constructor() {
        this.initializeChatInterface();
        this.initializePortfolioInterface();
    }

    initializeChatInterface() {
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.visualContent = document.getElementById('visual-content');
        
        this.initializeChatEventListeners();
    }

    initializePortfolioInterface() {
        this.portfolioMetrics = document.getElementById('portfolio-metrics');
        this.allocationChart = document.getElementById('allocation-chart');
        this.performanceChart = document.getElementById('performance-chart');
        
        this.loadPortfolioData();
    }

    initializeChatEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }

    async loadPortfolioData() {
        try {
            const [metricsResponse, allocationResponse, performanceResponse] = await Promise.all([
                fetch('/portfolio/metrics'),
                fetch('/portfolio/allocation'),
                fetch('/portfolio/performance')
            ]);

            const [metricsData, allocationData, performanceData] = await Promise.all([
                metricsResponse.json(),
                allocationResponse.json(),
                performanceResponse.json()
            ]);

            this.displayMetrics(metricsData);
            this.displayAllocationChart(allocationData);
            this.displayPerformanceChart(performanceData);
        } catch (error) {
            console.error('Error loading portfolio data:', error);
        }
    }

    displayMetrics(data) {
        if (!data.metrics) return;
        
        const metricsHtml = `
            <div class="metrics-grid">
                ${Object.entries(data.metrics).map(([label, value]) => `
                    <div class="metric-card">
                        <div class="metric-value ${value.startsWith('+') ? 'positive-change' : value.startsWith('-') ? 'negative-change' : ''}">
                            ${value}
                        </div>
                        <div class="metric-label">${label}</div>
                    </div>
                `).join('')}
            </div>
        `;
        
        this.portfolioMetrics.innerHTML = metricsHtml;
    }

    displayAllocationChart(data) {
        if (data.type !== 'chart') return;
        if (this.allocationChartInstance) {
            this.allocationChartInstance.destroy();
        }
        this.allocationChartInstance = new Chart(this.allocationChart, data.config);
    }

    displayPerformanceChart(data) {
        if (data.type !== 'chart') return;
        if (this.performanceChartInstance) {
            this.performanceChartInstance.destroy();
        }
        this.performanceChartInstance = new Chart(this.performanceChart, data.config);
    }

    addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
        messageDiv.textContent = message;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        this.addMessage(message, true);
        this.messageInput.value = '';
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();
            
            if (data.error) {
                this.addMessage('Sorry, there was an error processing your request.');
            } else {
                this.addMessage(data.response);
                if (data.visual_data) {
                    this.displayVisualData(data.visual_data);
                }
            }
        } catch (error) {
            this.addMessage('Sorry, there was an error connecting to the server.');
        }

        this.messageInput.disabled = false;
        this.sendButton.disabled = false;
        this.messageInput.focus();
    }

    displayVisualData(data) {
        if (!data) return;

        const visualContainer = document.createElement('div');
        visualContainer.className = 'visual-container mb-4';

        if (data.type === 'chart') {
            const canvas = document.createElement('canvas');
            visualContainer.appendChild(canvas);
            this.visualContent.appendChild(visualContainer);
            new Chart(canvas, data.config);
        } else if (data.type === 'metrics') {
            this.displayMetrics(data);
        } else if (data.type === 'table') {
            this.displayTable(data, visualContainer);
            this.visualContent.appendChild(visualContainer);
        }
    }

    displayTable(data, container) {
        const table = document.createElement('table');
        table.className = 'table table-hover';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        data.headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        data.rows.forEach(row => {
            const tr = document.createElement('tr');
            row.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        
        container.appendChild(table);
    }
}

// Initialize the dashboard interface when the document is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardInterface = new DashboardInterface();
});
