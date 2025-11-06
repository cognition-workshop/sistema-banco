document.addEventListener('DOMContentLoaded', function() {
    const passwordFields = document.querySelectorAll('input[type="password"]');
    passwordFields.forEach(field => {
        field.addEventListener('input', function() {
            validatePasswordStrength(this);
        });
    });

    const emailFields = document.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        field.addEventListener('blur', function() {
            validateEmail(this);
        });
    });

    const amountFields = document.querySelectorAll('input[name="amount"]');
    amountFields.forEach(field => {
        field.addEventListener('input', function() {
            validateAmount(this);
        });
    });
});

function validatePasswordStrength(field) {
    const password = field.value;
    const feedback = field.parentElement.querySelector('.password-feedback') || createFeedbackElement(field);

    const checks = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };

    const allValid = Object.values(checks).every(v => v);

    if (password.length > 0 && !allValid) {
        feedback.innerHTML = 'Password must contain: ' +
            (!checks.length ? '8+ characters, ' : '') +
            (!checks.uppercase ? 'uppercase, ' : '') +
            (!checks.lowercase ? 'lowercase, ' : '') +
            (!checks.number ? 'number, ' : '') +
            (!checks.special ? 'special character' : '');
        feedback.className = 'text-yellow-600 text-sm italic';
    } else if (allValid) {
        feedback.innerHTML = 'Strong password ✓';
        feedback.className = 'text-green-600 text-sm italic';
    } else {
        feedback.innerHTML = '';
    }
}

function validateEmail(field) {
    const email = field.value;
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    if (email && !emailRegex.test(email)) {
        showFieldError(field, 'Please enter a valid email address');
    } else {
        clearFieldError(field);
    }
}

function validateAmount(field) {
    const amount = parseFloat(field.value);

    if (isNaN(amount) || amount <= 0) {
        showFieldError(field, 'Amount must be a positive number');
    } else if (amount > 999999999.99) {
        showFieldError(field, 'Amount exceeds maximum allowed');
    } else {
        clearFieldError(field);
    }
}

function createFeedbackElement(field) {
    const feedback = document.createElement('p');
    feedback.className = 'password-feedback';
    field.parentElement.appendChild(feedback);
    return feedback;
}

function showFieldError(field, message) {
    clearFieldError(field);
    const error = document.createElement('p');
    error.className = 'field-error text-red-600 text-sm italic';
    error.textContent = message;
    field.parentElement.appendChild(error);
    field.classList.add('border-red-500');
}

function clearFieldError(field) {
    const error = field.parentElement.querySelector('.field-error');
    if (error) error.remove();
    field.classList.remove('border-red-500');
}
