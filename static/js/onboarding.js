let currentStep = 1;
const totalSteps = 4;

function showOnboarding() {
    if (!localStorage.getItem('onboardingComplete')) {
        const modal = document.getElementById('onboardingModal');
        if (modal) {
            modal.classList.remove('hidden');
            updateStepIndicators();
        }
    }
}

function nextOnboardingStep() {
    document.getElementById('onboardingStep' + currentStep).classList.add('hidden');
    currentStep++;
    if (currentStep <= totalSteps) {
        document.getElementById('onboardingStep' + currentStep).classList.remove('hidden');
        updateStepIndicators();
    }
}

function previousOnboardingStep() {
    document.getElementById('onboardingStep' + currentStep).classList.add('hidden');
    currentStep--;
    if (currentStep >= 1) {
        document.getElementById('onboardingStep' + currentStep).classList.remove('hidden');
        updateStepIndicators();
    }
}

function completeOnboarding() {
    localStorage.setItem('onboardingComplete', 'true');
    const modal = document.getElementById('onboardingModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

function skipOnboarding() {
    completeOnboarding();
}

function updateStepIndicators() {
    const indicators = document.querySelectorAll('.step-indicator');
    indicators.forEach((indicator, index) => {
        if (index + 1 === currentStep) {
            indicator.classList.remove('bg-gray-300');
            indicator.classList.add('bg-primary');
        } else if (index + 1 < currentStep) {
            indicator.classList.remove('bg-gray-300');
            indicator.classList.add('bg-accent');
        } else {
            indicator.classList.remove('bg-primary', 'bg-accent');
            indicator.classList.add('bg-gray-300');
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(showOnboarding, 1000);
});
