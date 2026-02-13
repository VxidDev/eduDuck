export const CustomModel = document.getElementById("customModel");
export const CustomModelInput = document.querySelector(".customModelInput");
export const APIModeSelector = document.getElementById("apiMode");
export const UserInput = document.getElementById("user-input");
export const ApiKeyInput = document.querySelector(".apiKey");
export const ApiKeyInputParent = ApiKeyInput ? ApiKeyInput.closest('.textInput-wrapper') : null;
export const sendButton = document.getElementById("send-button");
export const ChatMessages = document.getElementById("chat-messages");
export const NewChat = document.getElementById("new-chat");
export const FreeUsage = document.getElementById("FreeUsage");
export const FreeUsageText = document.getElementById("FreeUsageText");
export const LanguageSelector = document.getElementById("output-language");
const StatusWrapper = document.querySelector('.status-wrapper');
const Spinner = document.querySelector('.spinner');
const StatusText = document.querySelector('.status-text');
export function showSpinner() {
    StatusWrapper.classList.remove('hidden');
    Spinner.classList.remove('hidden');
    StatusText.classList.add('hidden');
    StatusText.textContent = '';
}
export function showStatus(msg) {
    StatusWrapper.classList.remove('hidden');
    StatusText.classList.remove('hidden');
    StatusText.textContent = msg;
    Spinner.classList.add('hidden');
}
export function hideStatus() {
    StatusWrapper.classList.add('hidden');
    Spinner.classList.add('hidden');
    StatusText.classList.add('hidden');
}
export function renderMessage(role, content) {
    ChatMessages.innerHTML += `
        <div class="message ${role === "assistant" ? "ai" : "user"}-message">
            <div class="message-bubble">${content}</div>
        </div>`;
    ChatMessages.scrollTop = ChatMessages.scrollHeight;
}
//# sourceMappingURL=ui.js.map