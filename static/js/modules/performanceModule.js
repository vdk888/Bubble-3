// Performance Module
import { formatCurrency, formatPercentage } from './uiModule.js';

export class PerformanceModule {
    constructor() {
        this.chart = null;
        this.currentTimeframe = '1D';
        this.performanceSection = document.getElementById('performance-section');
        this.toggleButton = document.getElementById('toggle-performance');
        this.currentView = 'chart'; // 'chart' or 'table'
        this.toggleViewButton = document.getElementById('toggle-view');
        this.chartContainer = null;
        this.tableContainer = null;
        this.performanceTable = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Toggle performance section
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', () => {
                const isHidden = !this.performanceSection.classList.contains('slide-open');
                if (isHidden) {
                    this.performanceSection.style.display = 'block';
                    // Trigger reflow
                    this.performanceSection.offsetHeight;
                    this.performanceSection.classList.add('slide-open');
                    this.loadPerformanceData(this.currentTimeframe);
                } else {
                    this.performanceSection.classList.remove('slide-open');
                    setTimeout(() => {
                        this.performanceSection.style.display = 'none';
                    }, 500); // Match transition duration
                }
            });
        }

        // Timeframe buttons
        const timeframeButtons = document.querySelectorAll('.timeframe-btn');
        timeframeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                timeframeButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                this.currentTimeframe = button.dataset.timeframe;
                this.loadPerformanceData(this.currentTimeframe);
            });
        });

        // Initial load if section is visible
        if (this.performanceSection && this.performanceSection.style.display !== 'none') {
            this.loadPerformanceData(this.currentTimeframe);
        }

        // Add toggle view button listener
        if (this.toggleViewButton) {
            this.toggleViewButton.addEventListener('click', () => {
                this.toggleView();
            });
        }

        // Store references to containers
        this.chartContainer = document.querySelector('.performance-chart-container');
        this.tableContainer = document.querySelector('.performance-table-container');
        this.performanceTable = document.getElementById('performance-table');
    }

    getTimeframeParams(timeframe) {
        return `timeframe=${timeframe}`;  // Just pass the timeframe button value directly
    }

    async loadPerformanceData(timeframe) {
        try {
            const response = await fetch(`/api/portfolio/history?timeframe=${timeframe}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading performance data:', data.error);
                return;
            }

            // Ensure we have matching timestamps and equity values
            if (!data.timestamp || !data.equity || data.timestamp.length !== data.equity.length) {
                console.error('Invalid performance data format:', data);
                return;
            }

            // Filter out any null or invalid values
            const validDataPoints = data.timestamp.reduce((acc, ts, index) => {
                const equity = data.equity[index];
                if (ts && equity !== null && !isNaN(equity)) {
                    acc.push({
                        x: new Date(ts * 1000),
                        y: equity
                    });
                }
                return acc;
            }, []);

            // Sort data points by timestamp
            const sortedDataPoints = validDataPoints.sort((a, b) => a.x - b.x);

            // Update the chart and table with the cleaned data
            this.updateChart(sortedDataPoints, timeframe);
            this.updateStats({
                total_return: data.profit_loss_pct[data.profit_loss_pct.length - 1] * 100,
                history: {
                    equity: data.equity.filter(val => val !== null && !isNaN(val))
                }
            });
        } catch (error) {
            console.error('Error loading performance data:', error);
        }
    }

    updateChart(dataPoints, timeframe) {
        const ctx = document.getElementById('performance-chart');
        
        if (!ctx) {
            console.error('Performance chart canvas not found');
            return;
        }
        
        if (this.chart) {
            this.chart.destroy();
        }

        const unit = this.getTimeUnit(timeframe);
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Portfolio Value',
                    data: dataPoints,
                    borderColor: '#4CAF50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleColor: '#fff',
                        titleFont: {
                            size: 14,
                            weight: 'normal'
                        },
                        bodyColor: '#fff',
                        bodyFont: {
                            size: 14
                        },
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return formatCurrency(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: unit,
                            displayFormats: {
                                minute: 'HH:mm',
                                hour: 'HH:mm',
                                day: 'MMM d',
                                week: 'MMM d',
                                month: 'MMM yyyy'
                            },
                            tooltipFormat: this.getTooltipFormat(timeframe)
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        border: {
                            color: 'rgba(255, 255, 255, 0.2)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            maxRotation: 0,
                            autoSkip: true,
                            maxTicksLimit: 8,
                            padding: 8
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        border: {
                            color: 'rgba(255, 255, 255, 0.2)'
                        },
                        ticks: {
                            color: 'rgba(255, 255, 255, 0.7)',
                            padding: 8,
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });

        // Update table view
        this.updateTable(dataPoints);
    }

    getTimeUnit(timeframe) {
        switch(timeframe) {
            case '1D': return 'hour';
            case '1W': return 'day';
            case '1M': return 'day';
            case '3M': return 'day';
            case '1Y': return 'month';
            case 'ALL': return 'month';
            default: return 'hour';
        }
    }

    getTooltipFormat(timeframe) {
        switch(timeframe) {
            case '1D': return 'MMM d, HH:mm';
            case '1W': return 'MMM d, HH:mm';
            case '1M': return 'MMM d, HH:mm';
            case '3M': return 'MMM d, HH:mm';
            case '1Y': return 'MMM d, yyyy';
            case 'ALL': return 'MMM d, yyyy';
            default: return 'MMM d, HH:mm';
        }
    }

    updateStats(data) {
        const totalReturn = document.getElementById('total-return');
        const periodHigh = document.getElementById('period-high');
        const periodLow = document.getElementById('period-low');

        if (totalReturn) {
            const returnValue = data.total_return;
            totalReturn.textContent = formatPercentage(returnValue);
            totalReturn.className = 'stat-value ' + (returnValue >= 0 ? 'positive' : 'negative');
        }

        if (periodHigh) {
            const highValue = Math.max(...data.history.equity);
            periodHigh.textContent = formatCurrency(highValue);
        }

        if (periodLow) {
            const lowValue = Math.min(...data.history.equity);
            periodLow.textContent = formatCurrency(lowValue);
        }
    }

    toggleView() {
        if (this.currentView === 'chart') {
            this.currentView = 'table';
            this.chartContainer.style.display = 'none';
            this.tableContainer.style.display = 'block';
            this.toggleViewButton.innerHTML = '<i class="fas fa-chart-area"></i>';
        } else {
            this.currentView = 'chart';
            this.chartContainer.style.display = 'block';
            this.tableContainer.style.display = 'none';
            this.toggleViewButton.innerHTML = '<i class="fas fa-table"></i>';
        }
    }

    updateTable(dataPoints) {
        if (!this.performanceTable) return;

        const tbody = this.performanceTable.querySelector('tbody');
        tbody.innerHTML = '';

        // Sort data points by date in descending order
        const sortedData = [...dataPoints].sort((a, b) => b.x - a.x);

        sortedData.forEach((point, index) => {
            const row = document.createElement('tr');
            const date = point.x.toLocaleString();
            const value = formatCurrency(point.y);
            
            // Calculate change from previous point
            let change = '';
            if (index < sortedData.length - 1) {
                const changeValue = ((point.y - sortedData[index + 1].y) / sortedData[index + 1].y) * 100;
                const changeClass = changeValue >= 0 ? 'positive' : 'negative';
                change = `<span class="${changeClass}">${formatPercentage(changeValue)}</span>`;
            }

            row.innerHTML = `
                <td>${date}</td>
                <td>${value}</td>
                <td>${change}</td>
            `;
            tbody.appendChild(row);
        });
    }
} 