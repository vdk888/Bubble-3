// Tools Module
import { formatCurrency, formatPercentage, getChartColor } from './uiModule.js';

export class ToolsModule {
    constructor() {
        this.toolContents = document.getElementById('tool-contents');
        this.toolButtons = document.querySelectorAll('.tool-button');
        this.positionsChart = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Listen for bot actions
        document.addEventListener('botAction', (event) => {
            this.handleBotAction(event.detail);
        });

        // Listen for tool selection
        document.addEventListener('toolSelected', (event) => {
            // Create appropriate chat message based on the selected tool
            let chatMessage;
            switch (event.detail) {
                case 'positions':
                    chatMessage = "Could you analyze my current portfolio positions and provide insights about my holdings?";
                    break;
                case 'orders':
                    chatMessage = "Please show me my recent orders and any patterns or trends you notice.";
                    break;
                case 'trade':
                    chatMessage = "I'd like to place a trade. Could you help me understand my current trading options?";
                    break;
                case 'analysis':
                    chatMessage = "Could you provide a detailed market analysis?";
                    break;
                case 'portfolio-performance':
                    chatMessage = "Please provide a comprehensive analysis of my portfolio performance. What are the key trends and metrics I should be aware of?";
                    break;
                default:
                    chatMessage = `Show me information about ${event.detail}`;
            }

            // Dispatch chat message event
            document.dispatchEvent(new CustomEvent('chatMessage', {
                detail: chatMessage
            }));

            // Show the tool
            this.showTool(event.detail);
        });
    }

    handleBotAction(action) {
        switch (action.type) {
            case 'show_positions':
                // Customize the message sent to chatbot for positions
                const positionsEvent = new CustomEvent('chatMessage', {
                    detail: "Could you analyze my current portfolio positions and provide insights about my holdings?"
                });
                document.dispatchEvent(positionsEvent);
                this.showTool('positions');
                break;
            case 'show_orders':
                const ordersEvent = new CustomEvent('chatMessage', {
                    detail: "Please show me my recent orders and any patterns or trends you notice."
                });
                document.dispatchEvent(ordersEvent);
                this.showTool('orders');
                break;
            case 'show_trade':
                const tradeEvent = new CustomEvent('chatMessage', {
                    detail: "I'd like to place a trade. Could you help me understand my current trading options?"
                });
                document.dispatchEvent(tradeEvent);
                this.showTool('trade');
                break;
            case 'show_analysis':
                this.showTool('total-assets');
                break;
            case 'show_custom_portfolio':
                const portfolioEvent = new CustomEvent('chatMessage', {
                    detail: "I'd like to explore custom portfolio options. What strategies would you recommend?"
                });
                document.dispatchEvent(portfolioEvent);
                this.showTool('custom-portfolio');
                break;
            case 'place_order':
                this.handleOrderPlacement(action.data);
                break;
            case 'analyze_symbol':
                this.handleSymbolAnalysis(action.data);
                break;
        }
    }

    showTool(toolName) {
        console.log('Showing tool:', toolName);
        
        if (!this.toolContents) {
            console.error('Tool contents container not found');
            return;
        }

        // Hide all tool contents first
        const allContents = document.querySelectorAll('.tool-content');
        allContents.forEach(content => {
            if (content) {
                content.style.display = 'none';
            }
        });

        // Show the tool contents container
        this.toolContents.style.display = 'block';

        // Show the specific tool content
        const content = document.getElementById(`${toolName}-content`);
        if (content) {
            content.style.display = 'block';
            console.log(`Showing ${toolName} content`);
        } else {
            console.error(`Content not found for tool: ${toolName}`);
        }

        // Update active state of tool buttons
        if (this.toolButtons) {
            this.toolButtons.forEach(button => {
                if (button.dataset.tool === toolName) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
            });
        }

        // Load data for the tool
        switch (toolName) {
            case 'positions':
                this.loadPositions();
                break;
            case 'orders':
                this.loadOrders();
                break;
            case 'trade':
                this.setupTradeForm();
                break;
            case 'total-assets':
                this.showTotalAssetsMessage();
                break;
            case 'custom-portfolio':
                this.showCustomPortfolioMessage();
                break;
        }
    }

    async loadPositions() {
        console.log('Loading positions...');
        const positionsData = document.getElementById('positions-data');
        const chartCanvas = document.getElementById('positions-chart');
        
        if (!positionsData || !chartCanvas) {
            console.error('Required elements not found:', {
                positionsData: !!positionsData,
                chartCanvas: !!chartCanvas
            });
            return;
        }

        try {
            positionsData.innerHTML = '<div class="loading">Loading positions...</div>';
            const response = await fetch('/api/portfolio/positions');
            const data = await response.json();
            
            if (data.error) {
                console.error('API returned error:', data.error);
                positionsData.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }

            if (!data.positions || !Array.isArray(data.positions)) {
                console.error('Invalid positions data:', data);
                positionsData.innerHTML = '<div class="error-message">Invalid positions data received</div>';
                return;
            }

            // Filter out positions with zero or very small market value
            const significantPositions = data.positions.filter(position => 
                parseFloat(position.market_value) > 0.01
            );

            this.renderPositionsList(positionsData, significantPositions);
            this.renderPositionsChart(chartCanvas, significantPositions);

        } catch (error) {
            console.error('Error loading positions:', error);
            positionsData.innerHTML = '<div class="error-message">Failed to load positions</div>';
        }
    }

    renderPositionsList(container, positions) {
        let html = '<div class="positions-list">';
        
        positions.forEach(position => {
            const marketValue = parseFloat(position.market_value);
            const unrealizedPL = parseFloat(position.unrealized_pl);
            const unrealizedPLPC = parseFloat(position.unrealized_plpc);
            const plClass = unrealizedPL >= 0 ? 'positive' : 'negative';
            
            html += `
                <div class="position-item">
                    <div class="position-header">
                        <span class="position-symbol">${position.symbol}</span>
                        <span class="position-qty">${parseFloat(position.qty).toFixed(8)} shares</span>
                    </div>
                    <div class="position-details">
                        <div class="detail">
                            <span class="label">Market Value:</span>
                            <span class="value">${formatCurrency(marketValue)}</span>
                        </div>
                        <div class="detail">
                            <span class="label">P/L:</span>
                            <span class="value ${plClass}">${formatCurrency(unrealizedPL)} (${formatPercentage(unrealizedPLPC)})</span>
                        </div>
                        <div class="detail">
                            <span class="label">Current Price:</span>
                            <span class="value">${formatCurrency(parseFloat(position.current_price))}</span>
                        </div>
                        <div class="detail">
                            <span class="label">Avg Entry:</span>
                            <span class="value">${formatCurrency(parseFloat(position.avg_entry_price))}</span>
                        </div>
                    </div>
                </div>`;
        });
        html += '</div>';
        container.innerHTML = html;
    }

    renderPositionsChart(canvas, positions) {
        // Sort positions by market value in descending order
        const sortedPositions = [...positions].sort((a, b) => 
            parseFloat(b.market_value) - parseFloat(a.market_value)
        );

        const chartData = {
            labels: sortedPositions.map(p => p.symbol),
            values: sortedPositions.map(p => parseFloat(p.market_value)),
            colors: sortedPositions.map((_, i) => getChartColor(i))
        };

        const totalValue = chartData.values.reduce((a, b) => a + b, 0);
        
        if (totalValue > 0) {
            // Destroy existing chart if it exists
            if (this.positionsChart) {
                this.positionsChart.destroy();
            }

            const percentages = chartData.values.map(value => ((value / totalValue) * 100).toFixed(2));
            
            this.positionsChart = new Chart(canvas, {
                type: 'pie',
                data: {
                    labels: chartData.labels,
                    datasets: [{
                        data: chartData.values,
                        backgroundColor: chartData.colors,
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    layout: {
                        padding: {
                            top: 30,
                            bottom: 10
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'right',
                            labels: {
                                color: '#ffffff',
                                padding: 20
                            }
                        },
                        title: {
                            display: true,
                            text: 'Portfolio Allocation',
                            color: '#ffffff',
                            font: {
                                size: 16
                            },
                            padding: {
                                top: 0,
                                bottom: 20
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = percentages[context.dataIndex];
                                    const marketValue = formatCurrency(chartData.values[context.dataIndex]);
                                    return `${label}: ${value}% (${marketValue})`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    async loadOrders() {
        const ordersData = document.getElementById('orders-data');
        try {
            const response = await fetch('/api/portfolio/orders');
            const data = await response.json();
            
            if (data.error) {
                ordersData.innerHTML = `<div class="error-message">${data.error}</div>`;
                return;
            }

            let html = '<div class="orders-list">';
            data.orders.forEach(order => {
                const priceDisplay = order.filled_avg_price ? 
                    formatCurrency(order.filled_avg_price) : 
                    'Not filled';

                const qtyDisplay = order.filled_qty ? 
                    `${order.filled_qty}/${order.qty}` : 
                    order.qty;

                html += `
                    <div class="order-item">
                        <div class="order-header">
                            <span class="order-symbol">${order.symbol}</span>
                            <span class="order-status ${order.status.toLowerCase()}">${order.status}</span>
                        </div>
                        <div class="order-details">
                            <div class="detail">
                                <span class="label">Type:</span>
                                <span class="value">${order.type} ${order.side}</span>
                            </div>
                            <div class="detail">
                                <span class="label">Quantity:</span>
                                <span class="value">${qtyDisplay} shares</span>
                            </div>
                            <div class="detail">
                                <span class="label">Price:</span>
                                <span class="value">${priceDisplay}</span>
                            </div>
                            <div class="detail">
                                <span class="label">Submitted:</span>
                                <span class="value">${new Date(order.submitted_at).toLocaleString()}</span>
                            </div>
                            ${order.filled_at ? `
                            <div class="detail">
                                <span class="label">Filled:</span>
                                <span class="value">${new Date(order.filled_at).toLocaleString()}</span>
                            </div>` : ''}
                        </div>
                    </div>`;
            });
            html += '</div>';
            ordersData.innerHTML = html;
            ordersData.classList.remove('loading');
        } catch (error) {
            ordersData.innerHTML = '<div class="error-message">Failed to load orders</div>';
        }
    }

    setupTradeForm() {
        const tradeForm = document.getElementById('trade-form');
        const typeSelect = document.getElementById('trade-type');
        
        this.createPriceInputs(tradeForm, typeSelect);
        this.setupTradeFormSubmission();
    }

    createPriceInputs(tradeForm, typeSelect) {
        const limitPriceGroup = document.createElement('div');
        limitPriceGroup.className = 'form-group';
        limitPriceGroup.innerHTML = `
            <label for="limit-price">Limit Price</label>
            <input type="number" id="limit-price" class="dark-input" step="0.01" min="0">
        `;

        const stopPriceGroup = document.createElement('div');
        stopPriceGroup.className = 'form-group';
        stopPriceGroup.innerHTML = `
            <label for="stop-price">Stop Price</label>
            <input type="number" id="stop-price" class="dark-input" step="0.01" min="0">
        `;

        typeSelect.addEventListener('change', function() {
            const existingLimitPrice = tradeForm.querySelector('#limit-price');
            const existingStopPrice = tradeForm.querySelector('#stop-price');
            if (existingLimitPrice) existingLimitPrice.parentElement.remove();
            if (existingStopPrice) existingStopPrice.parentElement.remove();

            switch(this.value) {
                case 'limit':
                    typeSelect.parentElement.after(limitPriceGroup);
                    break;
                case 'stop':
                    typeSelect.parentElement.after(stopPriceGroup);
                    break;
                case 'stop_limit':
                    typeSelect.parentElement.after(stopPriceGroup);
                    stopPriceGroup.after(limitPriceGroup);
                    break;
            }
        });
    }

    setupTradeFormSubmission() {
        const submitButton = document.getElementById('submit-trade');
        submitButton.addEventListener('click', async (e) => {
            e.preventDefault();
            
            const orderData = this.collectTradeFormData();
            if (!orderData) return;

            try {
                const response = await fetch('/api/portfolio/trade', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(orderData)
                });

                const data = await response.json();
                if (data.error) {
                    alert('Error placing order: ' + data.error);
                } else {
                    alert('Order placed successfully');
                    this.loadOrders();
                }
            } catch (error) {
                alert('Error placing order: ' + error.message);
            }
        });
    }

    collectTradeFormData() {
        const symbol = document.getElementById('trade-symbol').value;
        const qty = document.getElementById('trade-quantity').value;
        const side = document.getElementById('trade-side').value;
        const type = document.getElementById('trade-type').value;
        
        if (!symbol || !qty || !side || !type) {
            alert('Please fill in all required fields');
            return null;
        }

        const orderData = {
            symbol: symbol,
            qty: parseFloat(qty),
            side: side,
            type: type
        };

        switch(type) {
            case 'limit':
                const limitPrice = document.getElementById('limit-price').value;
                if (!limitPrice) {
                    alert('Please enter a limit price');
                    return null;
                }
                orderData.limit_price = parseFloat(limitPrice);
                break;
            case 'stop':
                const stopPrice = document.getElementById('stop-price').value;
                if (!stopPrice) {
                    alert('Please enter a stop price');
                    return null;
                }
                orderData.stop_price = parseFloat(stopPrice);
                break;
            case 'stop_limit':
                const stopLimitPrice = document.getElementById('stop-price').value;
                const stopLimitLimitPrice = document.getElementById('limit-price').value;
                if (!stopLimitPrice || !stopLimitLimitPrice) {
                    alert('Please enter both stop price and limit price');
                    return null;
                }
                orderData.stop_price = parseFloat(stopLimitPrice);
                orderData.limit_price = parseFloat(stopLimitLimitPrice);
                break;
        }

        return orderData;
    }

    async showTotalAssetsMessage() {
        const assetsData = document.getElementById('total-assets-content');
        if (!assetsData) return;

        try {
            // Fetch assets data
            const response = await fetch('/api/user/important-info?category=assets');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to fetch assets data');
            }

            let html = `
                <h3>Total Assets</h3>
                <div class="assets-container">
                    <div class="assets-list">`;

            if (data.data && data.data.length > 0) {
                data.data.forEach(asset => {
                    html += `
                        <div class="asset-item">
                            <div class="asset-content">${asset.content}</div>
                            <div class="asset-date">Last updated: ${new Date(asset.updated_at).toLocaleString()}</div>
                        </div>`;
                });
            } else {
                html += `
                    <div class="no-assets-message">
                        <p>No assets information found. You can add assets through the chat interface.</p>
                    </div>`;
            }

            html += `
                    </div>
                    <button id="show-all-info" class="secondary-button">
                        <i class="fas fa-eye"></i> Show All Information
                    </button>
                </div>`;

            assetsData.innerHTML = html;

            // Add event listener for the show all button
            const showAllBtn = document.getElementById('show-all-info');
            if (showAllBtn) {
                showAllBtn.addEventListener('click', () => this.toggleAllUserInfo());
            }

        } catch (error) {
            console.error('Error loading assets:', error);
            assetsData.innerHTML = `
                <div class="error-message">
                    <p>Error loading assets information. Please try again later.</p>
                </div>`;
        }
    }

    async toggleAllUserInfo() {
        const assetsData = document.getElementById('total-assets-content');
        if (!assetsData) return;

        try {
            const response = await fetch('/api/user/important-info');
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to fetch user information');
            }

            // Group information by type
            const groupedInfo = {};
            data.data.forEach(info => {
                if (!groupedInfo[info.type]) {
                    groupedInfo[info.type] = [];
                }
                groupedInfo[info.type].push(info);
            });

            let html = `
                <h3>All User Information</h3>
                <div class="all-info-container">`;

            for (const [type, items] of Object.entries(groupedInfo)) {
                html += `
                    <div class="info-category">
                        <h4>${this._formatInfoType(type)}</h4>
                        ${items.map(item => `
                            <div class="info-item">
                                <div class="info-content">${item.content}</div>
                                <div class="info-date">Last updated: ${new Date(item.updated_at).toLocaleString()}</div>
                            </div>
                        `).join('')}
                    </div>`;
            }

            html += `
                    <button id="show-assets-only" class="secondary-button">
                        <i class="fas fa-chart-pie"></i> Show Assets Only
                    </button>
                </div>`;

            assetsData.innerHTML = html;

            // Add event listener for the show assets only button
            const showAssetsBtn = document.getElementById('show-assets-only');
            if (showAssetsBtn) {
                showAssetsBtn.addEventListener('click', () => this.showTotalAssetsMessage());
            }

        } catch (error) {
            console.error('Error loading all information:', error);
            assetsData.innerHTML = `
                <div class="error-message">
                    <p>Error loading user information. Please try again later.</p>
                </div>`;
        }
    }

    _formatInfoType(type) {
        return type
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    showCustomPortfolioMessage() {
        const customPortfolioData = document.getElementById('custom-portfolio-data');
        if (customPortfolioData) {
            customPortfolioData.innerHTML = `
                <div class="coming-soon-message">
                    <h3>🚀 Coming Soon!</h3>
                    <p>Our customized portfolio feature is currently under development. Stay tuned for personalized portfolio management tools!</p>
                </div>`;
        }
    }
} 