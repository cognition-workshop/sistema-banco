
class ModalManager {
    constructor() {
        this.activeModal = null;
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-trigger')) {
                const modalId = e.target.dataset.modal;
                this.openModal(modalId);
            }
            
            if (e.target.classList.contains('modal-close') || 
                e.target.classList.contains('modal-overlay')) {
                this.closeModal();
            }
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.closeModal();
            }
        });
    }
    
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
            this.activeModal = modal;
            document.body.style.overflow = 'hidden';
        }
    }
    
    closeModal() {
        if (this.activeModal) {
            this.activeModal.classList.remove('active');
            this.activeModal = null;
            document.body.style.overflow = '';
        }
    }
}

function showLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.classList.add('active');
    }
}

function hideLoading() {
    const overlay = document.querySelector('.loading-overlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

class ToastManager {
    constructor() {
        this.container = this.createContainer();
    }
    
    createContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = this.getIcon(type);
        toast.innerHTML = `
            <i class="fas ${icon} text-xl"></i>
            <div>${message}</div>
        `;
        
        this.container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }
    
    getIcon(type) {
        const icons = {
            success: 'fa-check-circle text-green-600',
            error: 'fa-exclamation-circle text-red-600',
            info: 'fa-info-circle text-blue-600',
            warning: 'fa-exclamation-triangle text-yellow-600'
        };
        return icons[type] || icons.info;
    }
}

class KeyboardShortcuts {
    constructor() {
        this.shortcuts = {
            '/': () => this.focusSearch(),
            '?': () => this.showShortcutsModal(),
            'g h': () => window.location.href = '/',
            'g t': () => window.location.href = '/transactions/report/',
            'g d': () => window.location.href = '/transactions/deposit/',
            'g w': () => window.location.href = '/transactions/withdraw/'
        };
        
        this.keySequence = '';
        this.sequenceTimeout = null;
        this.setupListener();
    }
    
    setupListener() {
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }
            
            clearTimeout(this.sequenceTimeout);
            this.keySequence += e.key;
            
            if (this.shortcuts[this.keySequence]) {
                e.preventDefault();
                this.shortcuts[this.keySequence]();
                this.keySequence = '';
            } else if (this.shortcuts[e.key]) {
                e.preventDefault();
                this.shortcuts[e.key]();
                this.keySequence = '';
            } else {
                this.sequenceTimeout = setTimeout(() => {
                    this.keySequence = '';
                }, 1000);
            }
        });
    }
    
    focusSearch() {
        const searchInput = document.querySelector('.search-input');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    showShortcutsModal() {
        const modal = document.getElementById('shortcuts-modal');
        if (modal) {
            modal.classList.add('active');
        }
    }
}

class GlobalSearch {
    constructor() {
        this.searchInput = document.querySelector('.search-input');
        this.searchResults = document.querySelector('.search-results');
        
        if (this.searchInput) {
            this.setupSearch();
        }
    }
    
    setupSearch() {
        this.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            if (query.length > 2) {
                this.performSearch(query);
            } else {
                this.hideResults();
            }
        });
        
        this.searchInput.addEventListener('blur', () => {
            setTimeout(() => this.hideResults(), 200);
        });
    }
    
    performSearch(query) {
        const results = [
            { title: 'Transaction Report', url: '/transactions/report/', type: 'page' },
            { title: 'Deposit Money', url: '/transactions/deposit/', type: 'action' },
            { title: 'Withdraw Money', url: '/transactions/withdraw/', type: 'action' }
        ].filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase())
        );
        
        this.displayResults(results);
    }
    
    displayResults(results) {
        if (!this.searchResults) return;
        
        if (results.length === 0) {
            this.searchResults.innerHTML = '<div class="search-result-item">No results found</div>';
        } else {
            this.searchResults.innerHTML = results.map(result => `
                <div class="search-result-item" onclick="window.location.href='${result.url}'">
                    <div class="font-medium">${result.title}</div>
                    <div class="text-sm text-gray-500">${result.type}</div>
                </div>
            `).join('');
        }
        
        this.searchResults.classList.add('active');
    }
    
    hideResults() {
        if (this.searchResults) {
            this.searchResults.classList.remove('active');
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    window.modalManager = new ModalManager();
    window.toastManager = new ToastManager();
    window.keyboardShortcuts = new KeyboardShortcuts();
    window.globalSearch = new GlobalSearch();
    
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            showLoading();
        });
    });
});
