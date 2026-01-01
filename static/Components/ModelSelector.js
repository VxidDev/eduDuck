export function CustomModelListeners() {
    const CustomModel = document.getElementById('customModel');
    const CustomModelInput = document.querySelector('.customModelInput');
    const APIModeSelector = document.getElementById('apiMode');
    const ApiKeyInput = document.querySelector('.apiKey');
    const CustomModelSelector = document.querySelector('.customModelSelector');

    if (!CustomModel || !CustomModelInput || !APIModeSelector || !CustomModelSelector || !ApiKeyInput) {
        console.warn('UI elements not found');
        return;
    }

    CustomModel.addEventListener('change', () => {
        if (CustomModel.checked) {
            CustomModelInput.classList.remove('hidden');
        } else {
            CustomModelInput.classList.add('hidden');
        }
    });

    APIModeSelector.addEventListener('change', () => {
        ApiKeyInput.placeholder = `Enter your ${APIModeSelector.value} API key here!`;
        if (APIModeSelector.value !== 'Hugging Face') {
            CustomModelSelector.classList.add('hidden');
            CustomModelInput.classList.add('hidden');
        } else {
            if (CustomModel.checked) CustomModelInput.classList.remove('hidden');
            CustomModelSelector.classList.remove('hidden');
        }
    });
}
