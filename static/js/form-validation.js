document.addEventListener('DOMContentLoaded', function() {
    const amountInputs = document.querySelectorAll('input[name="amount"]');
    amountInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            const min = parseFloat(this.min) || 0;
            const max = parseFloat(this.max) || Infinity;
            
            if (isNaN(value) || value < min) {
                this.setCustomValidity(`Valor mínimo: ${min} $`);
            } else if (value > max) {
                this.setCustomValidity(`Valor máximo: ${max} $`);
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    const cpfInputs = document.querySelectorAll('input[data-cpf]');
    cpfInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const cpf = this.value.replace(/[^0-9]/g, '');
            if (cpf.length !== 11) {
                this.setCustomValidity('CPF deve conter 11 dígitos');
            } else {
                this.setCustomValidity('');
            }
        });
    });
    
    const emailInputs = document.querySelectorAll('input[type="email"]');
    emailInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(this.value)) {
                this.setCustomValidity('Email inválido');
            } else {
                this.setCustomValidity('');
            }
        });
    });
});
