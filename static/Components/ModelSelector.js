CustomModel.addEventListener('change', () => {
    if (CustomModel.checked) {
        CustomModelInput.classList.remove("hidden");
    } else {
        CustomModelInput.classList.add("hidden");
    }
});

APIModeSelector.addEventListener('change', () => {
    ApiKeyInput.placeholder = `Enter your ${APIModeSelector.value} API key here!`;
    if (APIModeSelector.value !== 'Hugging Face') {
        CustomModelSelector.classList.add('hidden');
        CustomModelInput.classList.add('hidden');
    } else {
        if (CustomModel.checked) CustomModelInput.classList.remove('hidden')
        CustomModelSelector.classList.remove('hidden')
    }
});