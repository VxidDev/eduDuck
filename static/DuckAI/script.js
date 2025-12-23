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

let IsHuggingFace = true;

let Messages = [];

function autoResize(input) {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 150) + 'px';
}

UserInput.addEventListener('input', function() {
    autoResize(this);
});

CustomModel.addEventListener('change', () => {
    if (CustomModel.checked) {
        CustomModelInput.classList.remove("hidden");
    } else {
        CustomModelInput.classList.add("hidden");
    }
});

APIModeSelector.addEventListener('change' , () => {
    ApiKeyInput.placeholder = `Enter your ${APIModeSelector.value} API key here!`;
    IsHuggingFace = APIModeSelector.value == "Hugging Face" ? true : false;
    if (!IsHuggingFace) {
        if (CustomModel.checked) {
            CustomModel.checked = false;
            CustomModelInput.classList.add("hidden");
        }
        CustomModel.classList.add("hidden");
        CustomModelLabel.classList.add("hidden");
        APIModeSelector.style.marginTop = "50px";
    } else {
        APIModeSelector.style.marginTop = null;
        CustomModel.classList.remove("hidden");
        CustomModelLabel.classList.remove("hidden");
    };
})

sendButton.addEventListener('click', async () => {
    StatusLabel.textContent = "";

    Messages.push({
        "role": "user",
        "content": userInput.value.trim()
    });

    ChatMessages.innerHTML += `<div class="message user-message"><div class="message-bubble">${UserInput.value.trim()}</div></div>`;

    const message = Messages.slice(-10).map(m => `${m.role}: ${m.content}`).join('\n');
    const apiKey = ApiKeyInput.value.trim();
    let model = null;

    UserInput.value = "";

    let msg = !apiKey ? "Enter API key."
        : !message ? "Enter message first."
        : message.split(' ').length > 2500 ? "Message is too long."
        : "Generating...";

    if (!CustomModelInput.classList.contains("hidden")) {
        model = CustomModelInput.value.trim();
        if (!model) {
            msg = "Enter model.";
        }
    } else {
        model = null;
    }

    StatusLabel.textContent = msg;
    if (!message || !apiKey || message.split(' ').length > 2500 || (!model && CustomModel.checked)) return;

    try {
        const body = {
            message: message,
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
        
        ChatMessages.innerHTML += `<div class="message ai-message"><div class="message-bubble">${data.response}</div></div>`;

        Messages.push({
            "role": "assistant",
            "content": data.response.trim()
        }); 

        StatusLabel.textContent = "";

    } catch (error) {
        StatusLabel.textContent = "Error while generating response.";
    }
});

NewChat.addEventListener('click', () => {
    window.location = `/duck-ai`
});

autoResize(UserInput);