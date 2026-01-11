import { ValidateInput } from "../Components/ValidateInput.js";
import { autoResize } from "../Components/AutoResize.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js"

const CustomModel = document.getElementById("customModel");
const CustomModelInput = document.querySelector(".customModelInput");
const APIModeSelector = document.getElementById("apiMode");
const UserInput = document.getElementById("user-input");
const ApiKeyInput = document.querySelector(".apiKey");
const sendButton = document.querySelector(".submit");
const ChatMessages = document.getElementById("chat-messages");
const StatusLabel = document.querySelector(".status");
const NewChat = document.getElementById("new-chat");
const FreeLimitBar = document.querySelector(".FreeLimit");
const FreeUsage = document.getElementById("FreeUsage");

let Messages = [];

sendButton.disabled = true;
CustomModelListeners();
GetFreeLimitUsage(FreeLimitBar , sendButton);

UserInput.addEventListener("input", function () {
	sendButton.disabled = !this.value.trim() || ((parseInt(FreeLimitBar.textContent[0]) >= 3) && FreeUsage.checked);
	autoResize(this);
});

sendButton.addEventListener("click", async () => {
	StatusLabel.textContent = "";
	sendButton.disabled = true;

	const text = UserInput.value.trim();
	const words = text.split(" ");
	const apiKey = ApiKeyInput.value.trim();
	const customModelVisible = !CustomModelInput.classList.contains("hidden");
	const modelValue = CustomModelInput.value.trim();

	ValidateInput(text, apiKey, customModelVisible, modelValue, StatusLabel, words , FreeUsage);

	if (
		(!apiKey && !FreeUsage.checked) ||
		!text ||
		words.length > 2500 ||
		(customModelVisible && CustomModel.checked && !modelValue)
	) {
		sendButton.disabled = false;
		return;
	}

	Messages.push({ role: "user", content: text });
	ChatMessages.innerHTML += `
		<div class="message user-message">
			<div class="message-bubble">${text}</div>
		</div>`;

	UserInput.value = "";

	const history = Messages.slice(-10)
		.map(m => `${m.role}: ${m.content}`)
		.join("\n");
	const model = customModelVisible && CustomModel.checked ? modelValue : null;

	try {
		const res = await fetch("/duck-ai/generate", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				message: history,
				apiKey: FreeUsage.checked ? null : apiKey,
				model: FreeUsage.checked ? null : model,
				apiMode: FreeUsage.checked ? "Gemini" : APIModeSelector.value.trim(),
				isFree: FreeUsage.checked
			})
		});

		const data = await res.json();

		ChatMessages.innerHTML += `
			<div class="message ai-message">
				<div class="message-bubble">${data.response}</div>
			</div>`;

		Messages.push({ role: "assistant", content: data.response.trim() });
		StatusLabel.textContent = "";
	} catch {
		StatusLabel.textContent = "Error while generating response.";
	} finally {
		GetFreeLimitUsage(FreeLimitBar , sendButton);
		if (parseInt(FreeLimitBar.textContent[0]) >= 3) sendButton.disabled = true;
	}
});

NewChat.addEventListener("click", () => (window.location = "/duck-ai"));
autoResize(UserInput);
