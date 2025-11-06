let touchStartX = 0;
let touchEndX = 0;
let touchStartY = 0;
let touchEndY = 0;

function initializeGestures() {
    document.addEventListener('touchstart', handleTouchStart, false);
    document.addEventListener('touchend', handleTouchEnd, false);
}

function handleTouchStart(e) {
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
}

function handleTouchEnd(e) {
    touchEndX = e.changedTouches[0].screenX;
    touchEndY = e.changedTouches[0].screenY;
    handleSwipe();
}

function handleSwipe() {
    const swipeThreshold = 50;
    const horizontalSwipe = touchEndX - touchStartX;
    const verticalSwipe = touchEndY - touchStartY;
    
    if (Math.abs(horizontalSwipe) > Math.abs(verticalSwipe)) {
        if (horizontalSwipe > swipeThreshold) {
            console.log('Swipe right detected');
        } else if (horizontalSwipe < -swipeThreshold) {
            console.log('Swipe left detected');
        }
    } else {
        if (verticalSwipe > swipeThreshold) {
            console.log('Swipe down detected');
        } else if (verticalSwipe < -swipeThreshold) {
            console.log('Swipe up detected');
        }
    }
}

document.addEventListener('DOMContentLoaded', initializeGestures);
