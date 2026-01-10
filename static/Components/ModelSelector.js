export function CustomModelListeners() {
    const CustomModel = document.getElementById('customModel');
    const CustomModelInput = document.querySelector('.customModelInput');
    const APIModeSelector = document.getElementById('apiMode');
    const ApiKeyInput = document.querySelector('.apiKey');
    const CustomModelSelector = document.querySelector('.customModelSelector');
    const FreeUsageSelector = document.getElementById("FreeUsage")
    const QuestionSelector = document.getElementById("questionCount");
    const FreeLimitBar = document.querySelector(".FreeLimit");
    const SubmitBtn = document.querySelector(".submit");

    if (!CustomModel || !CustomModelInput || !APIModeSelector || !CustomModelSelector || !ApiKeyInput || !FreeUsageSelector) {
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
            CustomModelSelector.style.display = "none";
            CustomModelInput.classList.add('hidden');
        } else {
            if (CustomModel.checked) CustomModelInput.classList.remove('hidden');
            CustomModelInput.placeholder = APIModeSelector.value === 'Hugging Face' ? "Enter custom model here! (e.g., microsoft/DialoGPT-medium)" : "Enter custom OpenAI model here! (e.g., gpt-4o-mini, gpt-4.1-nano)";
            CustomModelSelector.style.display = null;
        }
    });

    FreeUsageSelector.addEventListener('change' , () => {
        if (FreeUsageSelector.checked) {
            CustomModelSelector.style.display = "none";
            CustomModelInput.classList.add('hidden');
            ApiKeyInput.classList.add('hidden');
            APIModeSelector.classList.add('hidden');

            QuestionSelector.value = "5";
            QuestionSelector.disabled = "true";
            if (parseInt(FreeLimitBar.textContent[0]) >= 3) SubmitBtn.disabled = true; 
        } else {
            if (CustomModel.checked) CustomModelInput.classList.remove('hidden');
            if (APIModeSelector.value === 'Hugging Face' || APIModeSelector.value === "OpenAI") CustomModelSelector.style.display = null;
            ApiKeyInput.classList.remove('hidden');
            APIModeSelector.classList.remove('hidden');
            QuestionSelector.disabled = "false";
            SubmitBtn.disabled = false; 
        }
    });
}
