export function CustomModelListeners() {
    const customModelCheckbox = document.getElementById('customModel');
    const customModelInput = document.querySelector('.customModelInput');
    const apiModeSelector = document.getElementById('apiMode');
    const apiKeyInput = document.querySelector('.apiKey');
    const customModelSelector = document.querySelector('.customModelSelector');
    const freeUsageCheckbox = document.getElementById('FreeUsage');
    const questionSelector = document.getElementById('questionCount');
    const freeLimitBar = document.getElementById('FreeUsageText');
    const submitBtn = document.getElementById('send-button') || document.querySelector(".submit");

    if (!customModelCheckbox || !customModelInput || !apiModeSelector || !apiKeyInput || !customModelSelector) {
        console.warn('Core UI elements not found');
        return;
    }

    customModelCheckbox.addEventListener('change', () => {
        customModelInput.classList.toggle('hidden', !customModelCheckbox.checked);
    });

    apiModeSelector.addEventListener('change', () => {
        const mode = apiModeSelector.value;
        apiKeyInput.placeholder = `Enter your ${mode} API key here!`;

        if (mode !== 'Hugging Face' && mode !== 'OpenAI') {
            customModelSelector.style.display = 'none';
            customModelInput.classList.add('hidden');
        } else {
            customModelSelector.style.display = null;
            customModelInput.classList.toggle('hidden', !customModelCheckbox.checked);
            customModelInput.placeholder = mode === 'Hugging Face'
                ? "Enter custom model here! (e.g., microsoft/DialoGPT-medium)"
                : "Enter custom OpenAI model here! (e.g., gpt-4o-mini)";
        }
    });

    if (freeUsageCheckbox) {
        freeUsageCheckbox.addEventListener('change', () => {
            const isFree = freeUsageCheckbox.checked;

            [customModelSelector, customModelInput, apiKeyInput, apiModeSelector].forEach(el => {
                if (el) el.style.display = isFree ? 'none' : '';
            });

            if (questionSelector) questionSelector.disabled = isFree;
            submitBtn.disabled = isFree && freeLimitBar && parseInt(freeLimitBar.textContent[0]) >= 3;
        });
    }
}
