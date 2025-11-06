document.addEventListener('DOMContentLoaded', function() {
    const birthDateField = document.getElementById('id_birth_date');
    if (birthDateField) {
        birthDateField.addEventListener('blur', function() {
            validateAge(this);
        });
    }

    const nameFields = ['id_first_name', 'id_last_name'];
    nameFields.forEach(function(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.addEventListener('blur', function() {
                validateNameFormat(this);
            });
        }
    });

    const postalCodeField = document.getElementById('id_postal_code');
    if (postalCodeField) {
        postalCodeField.addEventListener('input', function() {
            formatCEP(this);
        });
        postalCodeField.addEventListener('blur', function() {
            validateCEP(this);
        });
    }

    const emailField = document.getElementById('id_email');
    if (emailField) {
        emailField.addEventListener('blur', function() {
            validateEmail(this);
        });
    }

    const password1 = document.getElementById('id_password1');
    const password2 = document.getElementById('id_password2');
    if (password1 && password2) {
        password1.addEventListener('blur', function() {
            validatePasswordStrength(this);
        });
        password2.addEventListener('blur', function() {
            validatePasswordMatch(password1, this);
        });
    }

    const amountField = document.getElementById('amount');
    if (amountField) {
        amountField.addEventListener('input', function() {
            validateAmount(this);
        });
    }

    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const invalidFields = form.querySelectorAll('.border-red-500');
            if (invalidFields.length > 0) {
                e.preventDefault();
                showError('Por favor, corrija os erros antes de enviar o formulário.');
                invalidFields[0].focus();
            }
        });
    });
});

function validateAge(field) {
    const birthDate = new Date(field.value);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    if (age < 18) {
        setFieldError(field, 'Você deve ter pelo menos 18 anos para abrir uma conta.');
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function validateNameFormat(field) {
    const namePattern = /^[A-Za-zÀ-ÿ\s]+$/;
    if (!namePattern.test(field.value)) {
        setFieldError(field, 'O nome deve conter apenas letras e espaços.');
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function formatCEP(field) {
    let value = field.value.replace(/\D/g, '');
    if (value.length > 5) {
        value = value.substring(0, 5) + '-' + value.substring(5, 8);
    }
    field.value = value;
}

function validateCEP(field) {
    const cepPattern = /^\d{5}-?\d{3}$/;
    if (!cepPattern.test(field.value)) {
        setFieldError(field, 'Formato de CEP inválido. Use: XXXXX-XXX');
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function validateEmail(field) {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(field.value)) {
        setFieldError(field, 'Email inválido.');
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function validatePasswordStrength(field) {
    const password = field.value;
    const errors = [];
    
    if (password.length < 8) {
        errors.push('mínimo 8 caracteres');
    }
    if (!/[A-Z]/.test(password)) {
        errors.push('letra maiúscula');
    }
    if (!/[a-z]/.test(password)) {
        errors.push('letra minúscula');
    }
    if (!/[0-9]/.test(password)) {
        errors.push('número');
    }
    
    if (errors.length > 0) {
        setFieldError(field, 'Senha deve conter: ' + errors.join(', '));
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function validatePasswordMatch(password1, password2) {
    if (password1.value !== password2.value) {
        setFieldError(password2, 'As senhas não coincidem.');
        return false;
    } else {
        setFieldValid(password2);
        return true;
    }
}

function validateAmount(field) {
    const value = parseFloat(field.value);
    const min = parseFloat(field.getAttribute('min')) || 10;
    
    if (isNaN(value) || value < min) {
        setFieldError(field, `Valor mínimo: ${min}`);
        return false;
    } else {
        setFieldValid(field);
        return true;
    }
}

function setFieldError(field, message) {
    field.classList.remove('border-gray-500', 'border-green-500');
    field.classList.add('border-red-500');
    
    const existingError = field.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
    
    const errorMsg = document.createElement('p');
    errorMsg.className = 'validation-error text-red-600 text-sm italic mt-1';
    errorMsg.textContent = message;
    field.parentElement.appendChild(errorMsg);
}

function setFieldValid(field) {
    field.classList.remove('border-red-500', 'border-gray-500');
    field.classList.add('border-green-500');
    
    const existingError = field.parentElement.querySelector('.validation-error');
    if (existingError) {
        existingError.remove();
    }
}

function showError(message) {
    alert(message);
}
