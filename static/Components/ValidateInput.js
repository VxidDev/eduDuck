export function ValidateInput(text , apiKey , customModelVisible , modelValue , StatusLabel , wordsCount , requiresApiKey) {
    let msg =
		!apiKey && requiresApiKey
			? "Enter API key."
			: !text
			? "Enter notes first."
			: wordsCount > 2500
			? "Notes too long."
			: customModelVisible && !model
			? "Enter model."
			: "Generating...";

    if (customModelVisible && CustomModel.checked && !modelValue) {
        msg = "Enter model.";
    }
    
    StatusLabel.textContent = msg;
}