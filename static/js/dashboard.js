document.addEventListener('DOMContentLoaded', function() {
    initializeTransactionChart();
    calculateStatistics();
    animateCounters();
});

function initializeTransactionChart() {
    const chartCanvas = document.getElementById('transactionChart');
    if (!chartCanvas) return;
    
    const transactionDataElement = document.getElementById('transaction-data');
    if (!transactionDataElement) return;
    
    try {
        const transactions = JSON.parse(transactionDataElement.textContent);
        
        if (transactions.length === 0) {
            return;
        }
        
        const labels = transactions.map(t => {
            const date = new Date(t.timestamp);
            return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
        });
        const balances = transactions.map(t => parseFloat(t.balance_after_transaction));
        
        const ctx = chartCanvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Saldo',
                    data: balances,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#3b82f6',
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
                        labels: {
                            font: {
                                size: 14,
                                weight: 'bold'
                            },
                            padding: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14,
                            weight: 'bold'
                        },
                        bodyFont: {
                            size: 13
                        },
                        callbacks: {
                            label: function(context) {
                                return 'Saldo: R$ ' + context.parsed.y.toFixed(2).replace('.', ',');
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value.toFixed(2).replace('.', ',');
                            },
                            font: {
                                size: 12
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 12
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    } catch (e) {
        console.error('Error initializing chart:', e);
    }
}

function calculateStatistics() {
    const transactionDataElement = document.getElementById('transaction-data');
    if (!transactionDataElement) return;
    
    try {
        const transactions = JSON.parse(transactionDataElement.textContent);
        
        let totalDeposits = 0;
        let totalWithdrawals = 0;
        
        transactions.forEach(transaction => {
            const amount = parseFloat(transaction.amount);
            if (transaction.transaction_type === 1) {
                totalDeposits += amount;
            } else if (transaction.transaction_type === 2) {
                totalWithdrawals += amount;
            }
        });
        
        const depositsElement = document.getElementById('total-deposits');
        const withdrawalsElement = document.getElementById('total-withdrawals');
        
        if (depositsElement) {
            depositsElement.textContent = totalDeposits.toFixed(2);
            depositsElement.setAttribute('data-target', totalDeposits.toFixed(2));
        }
        if (withdrawalsElement) {
            withdrawalsElement.textContent = totalWithdrawals.toFixed(2);
            withdrawalsElement.setAttribute('data-target', totalWithdrawals.toFixed(2));
        }
    } catch (e) {
        console.error('Error calculating statistics:', e);
    }
}

function animateCounters() {
    const counters = document.querySelectorAll('.counter');
    counters.forEach(counter => {
        const target = parseFloat(counter.textContent.replace(/[^\d.-]/g, ''));
        if (!isNaN(target)) {
            animateCounter(counter, target, 1500);
        }
    });
}

function animateCounter(element, target, duration) {
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        const current = start + (target - start) * easeOutQuad(progress);
        element.textContent = current.toFixed(2);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            element.textContent = target.toFixed(2);
        }
    }
    
    requestAnimationFrame(update);
}

function easeOutQuad(t) {
    return t * (2 - t);
}
