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
        if (APIModeSelector.value !== 'Hugging Face' && APIModeSelector.value !== "OpenAI") {
            CustomModelSelector.classList.add('hidden');
            CustomModelInput.classList.add('hidden');
        } else {
            if (CustomModel.checked) CustomModelInput.classList.remove('hidden');
            CustomModelInput.placeholder = APIModeSelector.value === 'Hugging Face' ? "Enter custom model here! (e.g., microsoft/DialoGPT-medium)" : "Enter custom OpenAI model here! (e.g., gpt-4o-mini, gpt-4.1-nano)";
            CustomModelSelector.classList.remove('hidden');
        }
    });
}
