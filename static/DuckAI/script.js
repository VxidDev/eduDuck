import { ValidateInput } from "../Components/ValidateInput.js";
import { autoResize } from "../Components/AutoResize.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";

const CustomModel = document.getElementById("customModel");
const CustomModelInput = document.querySelector(".customModelInput");
const APIModeSelector = document.getElementById("apiMode");
const UserInput = document.getElementById("user-input");
const ApiKeyInput = document.querySelector(".apiKey");
const sendButton = document.querySelector(".submit");
const ChatMessages = document.getElementById("chat-messages");
const StatusLabel = document.querySelector(".status");
const NewChat = document.getElementById("new-chat");

let Messages = [];

sendButton.disabled = true;
CustomModelListeners();

UserInput.addEventListener("input", function () {
	sendButton.disabled = !this.value.trim();
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

	ValidateInput(text, apiKey, customModelVisible, modelValue, StatusLabel, words);

	if (
		!apiKey ||
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
				apiKey,
				model,
				apiMode: APIModeSelector.value.trim()
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
		sendButton.disabled = false;
	}
});

NewChat.addEventListener("click", () => (window.location = "/duck-ai"));
autoResize(UserInput);
