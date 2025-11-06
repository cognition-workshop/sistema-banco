document.body.addEventListener('htmx:beforeRequest', function(evt) {
    const loadingEl = document.getElementById('loading-indicator');
    if (loadingEl) {
        loadingEl.style.display = 'flex';
    }
});

document.body.addEventListener('htmx:afterRequest', function(evt) {
    const loadingEl = document.getElementById('loading-indicator');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
});

document.body.addEventListener('htmx:responseError', function(evt) {
    const loadingEl = document.getElementById('loading-indicator');
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
    
    alert('An error occurred. Please try again.');
});

document.body.addEventListener('htmx:afterSwap', function(evt) {
    const messages = document.querySelectorAll('.auto-dismiss');
    messages.forEach(msg => {
        setTimeout(() => {
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 300);
        }, 3000);
    });
});
