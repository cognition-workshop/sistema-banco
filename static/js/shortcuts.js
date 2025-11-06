function initializeShortcuts() {
    document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
            e.preventDefault();
            window.location.href = '/transactions/deposit/';
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'w') {
            e.preventDefault();
            window.location.href = '/transactions/withdraw/';
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
            e.preventDefault();
            window.location.href = '/transactions/';
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
            e.preventDefault();
            window.location.href = '/';
        }
        
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('globalSearch');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        if (e.key === '?' && !e.shiftKey) {
            e.preventDefault();
            const modal = document.getElementById('shortcutsModal');
            if (modal) {
                modal.classList.remove('hidden');
            }
        }
        
        if (e.key === 'Escape') {
            closeShortcutsModal();
            const onboardingModal = document.getElementById('onboardingModal');
            if (onboardingModal && !onboardingModal.classList.contains('hidden')) {
                skipOnboarding();
            }
        }
    });
}

function closeShortcutsModal() {
    const modal = document.getElementById('shortcutsModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

document.addEventListener('DOMContentLoaded', initializeShortcuts);
