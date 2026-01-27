import { ValidateInput } from "../Components/ValidateInput.js";
import { autoResize } from "../Components/AutoResize.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

const CustomModel = document.getElementById("customModel");
const CustomModelInput = document.querySelector(".customModelInput");
const APIModeSelector = document.getElementById("apiMode");
const UserInput = document.getElementById("user-input");
const ApiKeyInput = document.querySelector(".apiKey");
const sendButton = document.getElementById("send-button");
const ChatMessages = document.getElementById("chat-messages");
const StatusLabel = document.querySelector(".status");
const NewChat = document.getElementById("new-chat");
const FreeUsage = document.getElementById("FreeUsage");
const FreeUsageText = document.getElementById("FreeUsageText");

let FreeUsageLeft = 0;

let Messages = [];

sendButton.disabled = true;
CustomModelListeners();
( async () => { if (FreeUsageText) await GetFreeLimitUsage();

// Initial Fetch
if (FreeUsageText) {
	const request = await fetch('/get-usage' , {
		method: "GET",
		headers: { "Content-Type": "application/json" }
	});

	let usageData = await request.json();

	FreeUsageLeft = usageData.remaining || 0;
	if (FreeUsageLeft <= 0 && FreeUsage?.checked) sendButton.disabled = true;
	FreeUsageText.textContent = `Welcome, ${window.CURRENT_USERNAME}! You have ${FreeUsageLeft} free uses today.`;
}
//

function updateSendButton() {
    const hasText = UserInput.value.trim();
    const usageOk = !FreeUsage?.checked || FreeUsageLeft > 0;
    sendButton.disabled = !hasText || !usageOk;
}

UserInput.addEventListener("input", () => {
    autoResize(UserInput);
    updateSendButton();
});

sendButton.addEventListener("click", async () => {
	if (FreeUsage && FreeUsage?.checked && FreeUsageLeft <= 0) {
		StatusLabel.textContent = "No free uses left today.";
		updateSendButton();
		return;
	}

    StatusLabel.textContent = "";
    sendButton.disabled = true;

    const text = UserInput.value.trim();
    const words = text.split(" ");
    const apiKey = ApiKeyInput.value.trim();
    const useCustomModel = !CustomModelInput.classList.contains("hidden") && CustomModel.checked;
    const modelValue = CustomModelInput.value.trim();
    const requiresApiKey = !FreeUsage || !FreeUsage.checked;

    ValidateInput(text, apiKey, useCustomModel, modelValue, StatusLabel, words, requiresApiKey);

    if (!text || (!apiKey && requiresApiKey) || words.length > 2500 || (useCustomModel && !modelValue)) {
        updateSendButton();
        return;
    }

    Messages.push({ role: "user", content: text });
    ChatMessages.innerHTML += `
        <div class="message user-message">
            <div class="message-bubble">${text}</div>
        </div>`;
    UserInput.value = "";
    updateSendButton();

    const history = Messages.slice(-10).map(m => `${m.role}: ${m.content}`).join("\n");
    const model = useCustomModel ? modelValue : null;

    try {
        const res = await fetch("/duck-ai/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: history,
                apiKey: FreeUsage && FreeUsage?.checked ? null : apiKey,
                model: FreeUsage && FreeUsage?.checked ? null : model,
                apiMode: FreeUsage && FreeUsage?.checked ? "OpenAI" : APIModeSelector.value.trim(),
                isFree: FreeUsage && FreeUsage?.checked
            })
        });

        const data = await res.json();

        ChatMessages.innerHTML += `
            <div class="message ai-message">
                <div class="message-bubble">${data.response}</div>
            </div>`;

        Messages.push({ role: "assistant", content: data.response.trim() });
        StatusLabel.textContent = "";

        if (FreeUsageText && FreeUsage?.checked) {
			const request = await fetch('/get-usage' , {
				method: "GET",
				headers: { "Content-Type": "application/json" }
			});

			const usageData = await request.json();
			FreeUsageLeft = usageData.remaining || 0;
			FreeUsageText.textContent = `Welcome, ${window.CURRENT_USERNAME}! You have ${FreeUsageLeft} free uses today.`;

			if (FreeUsageLeft <= 0) sendButton.disabled = true; 
		}
    } catch {
        StatusLabel.textContent = "Error while generating response.";
    } finally {
        updateSendButton();
    }
});

NewChat.addEventListener("click", () => window.location = "/duck-ai");
autoResize(UserInput);

})();
