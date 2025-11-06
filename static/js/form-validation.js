(function() {
    'use strict';

    function validateAmount(input, minAmount, maxAmount) {
        const value = parseFloat(input.value);
        const errorDiv = input.nextElementSibling;

        if (isNaN(value) || value <= 0) {
            showError(input, errorDiv, 'Por favor, insira um valor válido maior que zero');
            return false;
        }

        if (minAmount && value < minAmount) {
            showError(input, errorDiv, `O valor mínimo é ${minAmount} $`);
            return false;
        }

        if (maxAmount && value > maxAmount) {
            showError(input, errorDiv, `O valor máximo é ${maxAmount} $`);
            return false;
        }

        hideError(input, errorDiv);
        return true;
    }

    function validateEmail(input) {
        const email = input.value.trim();
        const errorDiv = input.nextElementSibling;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailRegex.test(email)) {
            showError(input, errorDiv, 'Por favor, insira um email válido');
            return false;
        }

        hideError(input, errorDiv);
        return true;
    }

    function validateRequired(input) {
        const value = input.value.trim();
        const errorDiv = input.nextElementSibling;

        if (!value) {
            showError(input, errorDiv, 'Este campo é obrigatório');
            return false;
        }

        hideError(input, errorDiv);
        return true;
    }

    function showError(input, errorDiv, message) {
        input.classList.add('border-red-500');
        input.classList.remove('border-gray-200');
        
        if (!errorDiv || !errorDiv.classList.contains('validation-error')) {
            errorDiv = document.createElement('p');
            errorDiv.className = 'validation-error text-red-600 text-sm italic mt-1';
            input.parentNode.insertBefore(errorDiv, input.nextSibling);
        }
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    function hideError(input, errorDiv) {
        input.classList.remove('border-red-500');
        input.classList.add('border-gray-200');
        
        if (errorDiv && errorDiv.classList.contains('validation-error')) {
            errorDiv.style.display = 'none';
        }
    }

    window.FormValidation = {
        validateAmount,
        validateEmail,
        validateRequired
    };
})();
