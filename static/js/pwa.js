
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('ServiceWorker registered:', registration);
            })
            .catch(error => {
                console.log('ServiceWorker registration failed:', error);
            });
    });
}

let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    const installButton = document.querySelector('.install-app-btn');
    if (installButton) {
        installButton.style.display = 'block';
        installButton.addEventListener('click', () => {
            installButton.style.display = 'none';
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                }
                deferredPrompt = null;
            });
        });
    }
});

class SwipeDetector {
    constructor(element) {
        this.element = element;
        this.startX = 0;
        this.startY = 0;
        this.endX = 0;
        this.endY = 0;
        this.minSwipeDistance = 50;
        
        this.setupListeners();
    }
    
    setupListeners() {
        this.element.addEventListener('touchstart', (e) => {
            this.startX = e.touches[0].clientX;
            this.startY = e.touches[0].clientY;
        }, { passive: true });
        
        this.element.addEventListener('touchend', (e) => {
            this.endX = e.changedTouches[0].clientX;
            this.endY = e.changedTouches[0].clientY;
            this.handleSwipe();
        }, { passive: true });
    }
    
    handleSwipe() {
        const deltaX = this.endX - this.startX;
        const deltaY = this.endY - this.startY;
        
        if (Math.abs(deltaX) > Math.abs(deltaY)) {
            if (Math.abs(deltaX) > this.minSwipeDistance) {
                if (deltaX > 0) {
                    this.onSwipeRight();
                } else {
                    this.onSwipeLeft();
                }
            }
        } else {
            if (Math.abs(deltaY) > this.minSwipeDistance) {
                if (deltaY > 0) {
                    this.onSwipeDown();
                } else {
                    this.onSwipeUp();
                }
            }
        }
    }
    
    onSwipeRight() {
        this.element.dispatchEvent(new CustomEvent('swiperight'));
    }
    
    onSwipeLeft() {
        this.element.dispatchEvent(new CustomEvent('swipeleft'));
    }
    
    onSwipeDown() {
        this.element.dispatchEvent(new CustomEvent('swipedown'));
    }
    
    onSwipeUp() {
        this.element.dispatchEvent(new CustomEvent('swipeup'));
    }
}

class PullToRefresh {
    constructor() {
        this.ptrElement = null;
        this.startY = 0;
        this.isPulling = false;
        this.threshold = 80;
        
        this.createPTRElement();
        this.setupListeners();
    }
    
    createPTRElement() {
        this.ptrElement = document.createElement('div');
        this.ptrElement.className = 'ptr-element';
        this.ptrElement.innerHTML = '<i class="fas fa-sync-alt"></i>';
        document.body.insertBefore(this.ptrElement, document.body.firstChild);
    }
    
    setupListeners() {
        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                this.startY = e.touches[0].clientY;
                this.isPulling = true;
            }
        }, { passive: true });
        
        document.addEventListener('touchmove', (e) => {
            if (this.isPulling) {
                const currentY = e.touches[0].clientY;
                const distance = currentY - this.startY;
                
                if (distance > 0) {
                    this.ptrElement.style.top = Math.min(distance - 60, 20) + 'px';
                    
                    if (distance > this.threshold) {
                        this.ptrElement.classList.add('active');
                    } else {
                        this.ptrElement.classList.remove('active');
                    }
                }
            }
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            if (this.isPulling) {
                const distance = this.ptrElement.offsetTop + 60;
                
                if (distance > this.threshold) {
                    this.refresh();
                }
                
                this.ptrElement.style.top = '-60px';
                this.ptrElement.classList.remove('active');
                this.isPulling = false;
            }
        }, { passive: true });
    }
    
    refresh() {
        window.location.reload();
    }
}

function updateOnlineStatus() {
    const statusElement = document.querySelector('.network-status');
    if (statusElement) {
        if (navigator.onLine) {
            statusElement.textContent = 'Online';
            statusElement.className = 'network-status online';
        } else {
            statusElement.textContent = 'Offline';
            statusElement.className = 'network-status offline';
        }
    }
}

window.addEventListener('online', updateOnlineStatus);
window.addEventListener('offline', updateOnlineStatus);

document.addEventListener('DOMContentLoaded', () => {
    const mainContent = document.querySelector('main') || document.body;
    const swipeDetector = new SwipeDetector(mainContent);
    
    mainContent.addEventListener('swiperight', () => {
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenu && window.innerWidth < 1024) {
            mobileMenu.classList.add('active');
        }
    });
    
    mainContent.addEventListener('swipeleft', () => {
        const mobileMenu = document.getElementById('mobile-menu');
        if (mobileMenu) {
            mobileMenu.classList.remove('active');
        }
    });
    
    if ('ontouchstart' in window) {
        new PullToRefresh();
    }
    
    updateOnlineStatus();
});
