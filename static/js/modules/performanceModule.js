// Performance Module
import { formatCurrency, formatPercentage } from './uiModule.js';

export class PerformanceModule {
    constructor() {
        this.chart = null;
        this.currentTimeframe = '1D';
        this.performanceSection = document.getElementById('performance-section');
        this.toggleButton = document.getElementById('toggle-performance');
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
    }

    getTimeframeParams(timeframe) {
        const params = new URLSearchParams();
        switch(timeframe) {
            case '1D':
                params.append('timeframe', '5Min');
                params.append('period', '1D');
                break;
            case '1W':
                params.append('timeframe', '1H');
                params.append('period', '1W');
                break;
            case '1M':
                params.append('timeframe', '1D');
                params.append('period', '1M');
                break;
            case '3M':
                params.append('timeframe', '1D');
                params.append('period', '3M');
                break;
            case '1Y':
                params.append('timeframe', '1D');
                params.append('period', '1A');
                break;
            case 'ALL':
                params.append('timeframe', '1D');
                params.append('period', 'all');
                break;
            default:
                params.append('timeframe', '5Min');
                params.append('period', '1D');
        }
        return params.toString();
    }

    async loadPerformanceData(timeframe) {
        try {
            const params = this.getTimeframeParams(timeframe);
            const response = await fetch(`/api/portfolio/history?${params}`);
            const data = await response.json();
            
            if (data.error) {
                console.error('Error loading performance data:', data.error);
                return;
            }

            console.log('Raw performance data:', data);

            // Create data points array
            const dataPoints = data.timestamp.map((ts, index) => ({
                x: new Date(ts * 1000),
                y: data.equity[index]
            }));

            console.log('Processed data points:', dataPoints);

            this.updateChart(dataPoints, timeframe);
            this.updateStats({
                total_return: data.profit_loss_pct[data.profit_loss_pct.length - 1] * 100,
                history: {
                    equity: data.equity
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
    }

    getTimeUnit(timeframe) {
        switch(timeframe) {
            case '1D': return 'hour';
            case '1W': return 'day';
            case '1M': return 'day';
            case '3M': return 'week';
            case '1Y': return 'month';
            case 'ALL': return 'month';
            default: return 'hour';
        }
    }

    getTooltipFormat(timeframe) {
        switch(timeframe) {
            case '1D': return 'HH:mm';
            case '1W': return 'MMM d, HH:mm';
            case '1M': return 'MMM d';
            case '3M': return 'MMM d';
            case '1Y': return 'MMM yyyy';
            case 'ALL': return 'MMM yyyy';
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
} 