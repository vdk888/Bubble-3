// Chart Module
import { formatCurrency, getChartColor } from './uiModule.js';

export class ChartModule {
    constructor() {
        this.loadChartJS();
    }

    loadChartJS() {
        if (!window.Chart) {
            const chartScript = document.createElement('script');
            chartScript.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            document.head.appendChild(chartScript);
        }
    }

    createPieChart(canvas, data, options = {}) {
        const defaultOptions = {
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
                    text: options.title || 'Chart',
                    color: '#ffffff',
                    font: {
                        size: 16
                    },
                    padding: {
                        top: 0,
                        bottom: 20
                    }
                }
            }
        };

        return new Chart(canvas, {
            type: 'pie',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: data.colors || data.values.map((_, i) => getChartColor(i)),
                    borderWidth: 1
                }]
            },
            options: { ...defaultOptions, ...options }
        });
    }

    createLineChart(canvas, data, options = {}) {
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                },
                title: {
                    display: true,
                    text: options.title || 'Chart',
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            }
        };

        return new Chart(canvas, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: data.datasets.map((dataset, index) => ({
                    label: dataset.label,
                    data: dataset.values,
                    borderColor: getChartColor(index),
                    backgroundColor: `${getChartColor(index)}33`,
                    tension: 0.4,
                    fill: true
                }))
            },
            options: { ...defaultOptions, ...options }
        });
    }

    createBarChart(canvas, data, options = {}) {
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                },
                title: {
                    display: true,
                    text: options.title || 'Chart',
                    color: '#ffffff',
                    font: {
                        size: 16
                    }
                }
            }
        };

        return new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: data.datasets.map((dataset, index) => ({
                    label: dataset.label,
                    data: dataset.values,
                    backgroundColor: getChartColor(index),
                    borderColor: getChartColor(index),
                    borderWidth: 1
                }))
            },
            options: { ...defaultOptions, ...options }
        });
    }

    destroyChart(chart) {
        if (chart) {
            chart.destroy();
        }
    }
} 