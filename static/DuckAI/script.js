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

// Initial Chat Parse If ID in DB and user is logined in.

const mainContent = document.querySelector(".main-content");
const initialChatData = mainContent?.dataset.chat;

if (initialChatData && initialChatData !== "" && initialChatData !== "null") {
    try {
        const parsedChat = JSON.parse(initialChatData);
        parsedChat.forEach(msg => {
            Messages.push(msg);
            ChatMessages.innerHTML += `
                <div class="message ${msg.role === "assistant" ? "ai" : "user"}-message">
                    <div class="message-bubble">${msg.content}</div>
                </div>`;
        });
        
        const urlParams = new URLSearchParams(window.location.search);
        const queryID = urlParams.get("id");
        if (parsedChat.length !== 0 && queryID) {
            window.CurrentDuckAIQueryID = queryID;
        }
        
        ChatMessages.scrollTop = ChatMessages.scrollHeight;

        mainContent.dataset.chat = '';
    } catch (err) {
        console.error("Failed to parse initial DuckAI chat:", err);
    }
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
        const botMessage = data.response.trim();

        Messages.push({ role: "assistant", content: botMessage });
        ChatMessages.innerHTML += `
            <div class="message ai-message">
                <div class="message-bubble">${botMessage}</div>
            </div>`;
        StatusLabel.textContent = "";

        if (window.CURRENT_USERNAME) {
            try {
                const storeRes = await fetch("/duck-ai/store-conversation", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        messages: [
                            { role: "user", content: text },
                            { role: "assistant", content: botMessage }
                        ],
                        queryID: window.CurrentDuckAIQueryID || null
                    })
                });

                if (storeRes.ok) {
                    const storeData = await storeRes.json();

                    if (storeData.queryID) {
                        if (!window.CurrentDuckAIQueryID) {
                            window.CurrentDuckAIQueryID = storeData.queryID;
                            window.history.pushState({}, "", `/duck-ai?id=${storeData.queryID}`);
                        }
                    } else {
                        console.warn("DuckAI store returned no queryID", storeData);
                    }
                } else {
                    console.error("DuckAI store failed:", storeRes.status, storeRes.statusText);
                }
            } catch (err) {
                console.error("DuckAI store conversation error:", err);
            }
        }

        if (FreeUsageText && FreeUsage?.checked) {
            const request = await fetch('/get-usage', { method: "GET", headers: { "Content-Type": "application/json" } });
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
