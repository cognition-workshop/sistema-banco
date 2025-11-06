document.addEventListener('DOMContentLoaded', function() {
    initFadeInAnimations();
    initMobileMenu();
    initCurrencyMasks();
});

function initFadeInAnimations() {
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach((el, index) => {
        el.style.opacity = '0';
        setTimeout(() => {
            el.style.opacity = '1';
        }, index * 100);
    });
}

function initMobileMenu() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function(e) {
            e.preventDefault();
            mobileMenu.classList.toggle('active');
        });
    }
}

function animateCounter(element, target, duration = 1000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = formatCurrency(target);
            clearInterval(timer);
        } else {
            element.textContent = formatCurrency(current);
        }
    }, 16);
}

function formatCurrency(value) {
    return value.toFixed(2).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function maskCurrency(input) {
    let value = input.value.replace(/\D/g, '');
    if (value === '') {
        input.value = '';
        return;
    }
    value = (parseFloat(value) / 100).toFixed(2);
    input.value = 'R$ ' + value.replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function initCurrencyMasks() {
    const amountInputs = document.querySelectorAll('input[name="amount"]');
    amountInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && !this.value.startsWith('R$')) {
                maskCurrency(this);
            }
        });
        
        input.addEventListener('focus', function() {
            if (this.value.startsWith('R$')) {
                const numericValue = this.value.replace(/[^\d,]/g, '').replace(',', '.');
                this.value = numericValue;
            }
        });
    });
}

function smoothScrollTo(element) {
    if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}
