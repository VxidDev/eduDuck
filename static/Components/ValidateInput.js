export function ValidateInput(text , apiKey , customModelVisible , modelValue , StatusLabel , wordsCount , FreeUsage) {
    let msg = !apiKey && !FreeUsage.checked ? "Enter API key."
        : !text ? "Enter message/notes first."
        : wordsCount > 2500 ? "Message/notes is too long."
        : "Generating...";

    if (customModelVisible && CustomModel.checked && !modelValue) {
        msg = "Enter model.";
    }
    
    StatusLabel.textContent = msg;
}