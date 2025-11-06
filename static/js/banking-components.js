
function calculateLoan() {
    const amount = parseFloat(document.getElementById('loan-amount')?.value) || 0;
    const rate = parseFloat(document.getElementById('loan-rate')?.value) || 0;
    const months = parseFloat(document.getElementById('loan-months')?.value) || 0;
    
    if (amount > 0 && rate > 0 && months > 0) {
        const monthlyRate = rate / 100 / 12;
        const monthlyPayment = amount * (monthlyRate * Math.pow(1 + monthlyRate, months)) / 
                              (Math.pow(1 + monthlyRate, months) - 1);
        const totalPayment = monthlyPayment * months;
        const totalInterest = totalPayment - amount;
        
        document.getElementById('loan-monthly-payment').textContent = 
            '$' + monthlyPayment.toFixed(2);
        document.getElementById('loan-total-payment').textContent = 
            '$' + totalPayment.toFixed(2);
        document.getElementById('loan-total-interest').textContent = 
            '$' + totalInterest.toFixed(2);
    }
}

function calculateInvestment() {
    const initial = parseFloat(document.getElementById('invest-initial')?.value) || 0;
    const monthly = parseFloat(document.getElementById('invest-monthly')?.value) || 0;
    const rate = parseFloat(document.getElementById('invest-rate')?.value) || 0;
    const years = parseFloat(document.getElementById('invest-years')?.value) || 0;
    
    if (initial >= 0 && rate > 0 && years > 0) {
        const monthlyRate = rate / 100 / 12;
        const months = years * 12;
        
        let futureValue = initial * Math.pow(1 + monthlyRate, months);
        
        if (monthly > 0) {
            futureValue += monthly * ((Math.pow(1 + monthlyRate, months) - 1) / monthlyRate);
        }
        
        const totalInvested = initial + (monthly * months);
        const totalEarnings = futureValue - totalInvested;
        
        document.getElementById('invest-future-value').textContent = 
            '$' + futureValue.toFixed(2);
        document.getElementById('invest-total-invested').textContent = 
            '$' + totalInvested.toFixed(2);
        document.getElementById('invest-total-earnings').textContent = 
            '$' + totalEarnings.toFixed(2);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const chatToggle = document.querySelector('.chat-toggle-btn');
    const chatWidget = document.querySelector('.chat-widget');
    const chatClose = document.querySelector('.chat-close-btn');
    const chatInput = document.querySelector('.chat-input');
    const chatMessages = document.querySelector('.chat-messages');
    
    if (chatToggle) {
        chatToggle.addEventListener('click', function() {
            chatWidget?.classList.toggle('active');
        });
    }
    
    if (chatClose) {
        chatClose.addEventListener('click', function() {
            chatWidget?.classList.remove('active');
        });
    }
    
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && this.value.trim()) {
                addChatMessage(this.value, 'user');
                this.value = '';
                
                setTimeout(() => {
                    addChatMessage('Thank you for your message. Our support team will assist you shortly.', 'bot');
                }, 1000);
            }
        });
    }
    
    function addChatMessage(text, sender) {
        if (!chatMessages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'chat-bubble';
        bubbleDiv.textContent = text;
        
        messageDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    const notificationBell = document.querySelector('.notification-bell');
    const notificationDropdown = document.querySelector('.notification-dropdown');
    
    if (notificationBell) {
        notificationBell.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationDropdown?.classList.toggle('active');
        });
    }
    
    document.addEventListener('click', function() {
        notificationDropdown?.classList.remove('active');
    });
    
    const loanInputs = ['loan-amount', 'loan-rate', 'loan-months'];
    loanInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', calculateLoan);
        }
    });
    
    const investInputs = ['invest-initial', 'invest-monthly', 'invest-rate', 'invest-years'];
    investInputs.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', calculateInvestment);
        }
    });
});
