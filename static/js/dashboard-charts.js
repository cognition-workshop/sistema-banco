function initDashboardCharts(transactionData, balanceHistory, monthlyData) {
    const chartColors = {
        primary: '#3B82F6',
        primaryDark: '#1E3A8A',
        success: '#059669',
        danger: '#DC2626',
        warning: '#F59E0B',
        background: 'rgba(59, 130, 246, 0.1)'
    };

    if (document.getElementById('balanceTrendChart')) {
        const ctx = document.getElementById('balanceTrendChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: balanceHistory.labels,
                datasets: [{
                    label: 'Account Balance',
                    data: balanceHistory.values,
                    borderColor: chartColors.primary,
                    backgroundColor: chartColors.background,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: chartColors.primary,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return 'Balance: $' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(0);
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    if (document.getElementById('transactionTypeChart')) {
        const ctx = document.getElementById('transactionTypeChart').getContext('2d');
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Deposits', 'Withdrawals', 'Interest'],
                datasets: [{
                    data: [
                        transactionData.deposits,
                        transactionData.withdrawals,
                        transactionData.interest
                    ],
                    backgroundColor: [
                        chartColors.success,
                        chartColors.danger,
                        chartColors.primary
                    ],
                    borderWidth: 3,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 13
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    if (document.getElementById('monthlyTransactionsChart')) {
        const ctx = document.getElementById('monthlyTransactionsChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: monthlyData.labels,
                datasets: [{
                    label: 'Transactions',
                    data: monthlyData.values,
                    backgroundColor: chartColors.primary,
                    borderColor: chartColors.primaryDark,
                    borderWidth: 1,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                return 'Transactions: ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}
