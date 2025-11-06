function calculateLoan() {
    const amount = parseInt(document.getElementById('loanAmount').value);
    const term = parseInt(document.getElementById('loanTerm').value);
    const annualRate = 0.12;
    const monthlyRate = annualRate / 12;
    
    const monthlyPayment = amount * (monthlyRate * Math.pow(1 + monthlyRate, term)) / (Math.pow(1 + monthlyRate, term) - 1);
    const totalPayment = monthlyPayment * term;
    
    document.getElementById('loanAmountDisplay').textContent = amount.toLocaleString('pt-BR');
    document.getElementById('loanTermDisplay').textContent = term;
    document.getElementById('monthlyPayment').textContent = monthlyPayment.toFixed(2).replace('.', ',');
    document.getElementById('totalPayment').textContent = totalPayment.toFixed(2).replace('.', ',');
}

function calculateInvestment() {
    const amount = parseInt(document.getElementById('investAmount').value);
    const term = parseInt(document.getElementById('investTerm').value);
    const annualRate = 0.10;
    const monthlyRate = annualRate / 12;
    
    const futureValue = amount * Math.pow(1 + monthlyRate, term);
    const earnings = futureValue - amount;
    
    document.getElementById('investAmountDisplay').textContent = amount.toLocaleString('pt-BR');
    document.getElementById('investTermDisplay').textContent = term;
    document.getElementById('futureValue').textContent = futureValue.toFixed(2).replace('.', ',');
    document.getElementById('earnings').textContent = earnings.toFixed(2).replace('.', ',');
}

function initializeCalculators() {
    if (document.getElementById('loanAmount')) {
        document.getElementById('loanAmount').addEventListener('input', calculateLoan);
        document.getElementById('loanTerm').addEventListener('input', calculateLoan);
        calculateLoan();
    }
    
    if (document.getElementById('investAmount')) {
        document.getElementById('investAmount').addEventListener('input', calculateInvestment);
        document.getElementById('investTerm').addEventListener('input', calculateInvestment);
        calculateInvestment();
    }
    
    if (document.getElementById('virtualCard')) {
        document.getElementById('virtualCard').addEventListener('click', function() {
            this.classList.toggle('flipped');
        });
    }
    
    const chatButton = document.getElementById('chatButton');
    const chatPanel = document.getElementById('chatPanel');
    const chatClose = document.getElementById('chatClose');
    const chatSend = document.getElementById('chatSend');
    const chatInput = document.getElementById('chatInput');
    
    if (chatButton) {
        chatButton.addEventListener('click', function() {
            chatPanel.classList.toggle('hidden');
        });
    }
    
    if (chatClose) {
        chatClose.addEventListener('click', function() {
            chatPanel.classList.add('hidden');
        });
    }
    
    if (chatSend && chatInput) {
        chatSend.addEventListener('click', function() {
            sendChatMessage();
        });
        
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
    
    const notificationButton = document.getElementById('notificationButton');
    const notificationPanel = document.getElementById('notificationPanel');
    
    if (notificationButton) {
        notificationButton.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationPanel.classList.toggle('hidden');
        });
        
        document.addEventListener('click', function() {
            if (!notificationPanel.classList.contains('hidden')) {
                notificationPanel.classList.add('hidden');
            }
        });
        
        notificationPanel.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }
}

function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const message = chatInput.value.trim();
    
    if (message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'flex items-start justify-end';
        messageElement.innerHTML = `
            <div class="bg-primary text-white p-3 rounded-lg shadow-sm max-w-xs">
                <p class="text-sm">${message}</p>
                <p class="text-xs opacity-75 mt-1">${new Date().toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}</p>
            </div>
        `;
        chatMessages.appendChild(messageElement);
        chatInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        setTimeout(function() {
            const responseElement = document.createElement('div');
            responseElement.className = 'flex items-start';
            responseElement.innerHTML = `
                <div class="bg-white p-3 rounded-lg shadow-sm max-w-xs">
                    <p class="text-sm">Obrigado pela sua mensagem! Um atendente responderá em breve.</p>
                    <p class="text-xs text-gray-500 mt-1">${new Date().toLocaleTimeString('pt-BR', {hour: '2-digit', minute: '2-digit'})}</p>
                </div>
            `;
            chatMessages.appendChild(responseElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 1000);
    }
}

document.addEventListener('DOMContentLoaded', initializeCalculators);
