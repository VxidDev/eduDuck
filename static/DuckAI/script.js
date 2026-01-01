const CustomModel = document.getElementById("customModel");
const CustomModelLabel = document.getElementById("customModelLabel");
const CustomModelInput = document.querySelector(".customModelInput");
const APIModeSelector = document.getElementById("apiMode");
const UserInput = document.getElementById('user-input');
const ApiKeyInput = document.querySelector(".apiKey");
const sendButton = document.querySelector(".submit");
const userInput = document.getElementById("user-input");
const ChatMessages = document.getElementById("chat-messages");
const StatusLabel = document.querySelector(".status");
const NewChat = document.getElementById("new-chat");

let Messages = [];

sendButton.disabled = true;

UserInput.addEventListener('input', function() {
    sendButton.disabled = userInput.value.trim().length === 0;
    autoResize(this);
});

sendButton.addEventListener('click', async () => {
    StatusLabel.textContent = "";
    sendButton.disabled = true;

    const text = userInput.value.trim();
    const apiKey = ApiKeyInput.value.trim();
    const customModelVisible = !CustomModelInput.classList.contains("hidden");
    const modelValue = CustomModelInput.value.trim();
    const wordsCount = text.split(/\s+/).filter(Boolean).length;

    let msg = !apiKey ? "Enter API key."
        : !text ? "Enter message first."
        : wordsCount > 2500 ? "Message is too long."
        : "Generating...";

    if (customModelVisible && CustomModel.checked && !modelValue) {
        msg = "Enter model.";
    }

    StatusLabel.textContent = msg;

    if (!apiKey || !text || wordsCount > 2500 || (customModelVisible && CustomModel.checked && !modelValue)) {
        sendButton.disabled = false;
        return;
    }

    Messages.push({
        role: "user",
        content: text
    });

    ChatMessages.innerHTML += `
        <div class="message user-message">
            <div class="message-bubble">${text}</div>
        </div>`;

    userInput.value = "";

    const history = Messages.slice(-10).map(m => `${m.role}: ${m.content}`).join('\n');
    const model = customModelVisible && CustomModel.checked ? modelValue : null;

    try {
        const body = {
            message: history,
            apiKey: apiKey,
            model: model,
            apiMode: APIModeSelector.value.trim()
        };

        const response = await fetch('/duck-ai/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        ChatMessages.innerHTML += `
            <div class="message ai-message">
                <div class="message-bubble">${data.response}</div>
            </div>`;

        Messages.push({
            role: "assistant",
            content: data.response.trim()
        });

        StatusLabel.textContent = "";
    } catch (error) {
        StatusLabel.textContent = "Error while generating response.";
    } finally {
        sendButton.disabled = false;
    }
});


NewChat.addEventListener('click', () => {
    window.location = `/duck-ai`
});

autoResize(UserInput);