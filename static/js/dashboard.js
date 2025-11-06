document.addEventListener('DOMContentLoaded', function() {
    const balanceChartCanvas = document.getElementById('balanceChart');
    if (balanceChartCanvas) {
        const balanceCtx = balanceChartCanvas.getContext('2d');
        
        const balanceData = JSON.parse(document.getElementById('balance-data').textContent);
        
        new Chart(balanceCtx, {
            type: 'line',
            data: {
                labels: balanceData.labels,
                datasets: [{
                    label: 'Account Balance',
                    data: balanceData.values,
                    borderColor: '#1976d2',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
    
    const transactionChartCanvas = document.getElementById('transactionChart');
    if (transactionChartCanvas) {
        const transactionCtx = transactionChartCanvas.getContext('2d');
        
        const transactionData = JSON.parse(document.getElementById('transaction-data').textContent);
        
        new Chart(transactionCtx, {
            type: 'doughnut',
            data: {
                labels: transactionData.labels,
                datasets: [{
                    data: transactionData.values,
                    backgroundColor: [
                        '#4caf50',
                        '#f44336',
                        '#2196f3'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
});
