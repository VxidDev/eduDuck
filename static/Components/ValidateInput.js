export function ValidateInput(text , apiKey , customModelVisible , modelValue , StatusLabel , wordsCount) {
    let msg = !apiKey ? "Enter API key."
        : !text ? "Enter message first."
        : wordsCount > 2500 ? "Message is too long."
        : "Generating...";

    if (customModelVisible && CustomModel.checked && !modelValue) {
        msg = "Enter model.";
    }
    
    StatusLabel.textContent = msg;
}