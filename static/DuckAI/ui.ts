export const CustomModel = document.getElementById("customModel") as HTMLInputElement;
export const CustomModelInput = document.querySelector<HTMLInputElement>(".customModelInput")!;
export const APIModeSelector = document.getElementById("apiMode") as HTMLSelectElement;
export const UserInput = document.getElementById("user-input") as HTMLTextAreaElement;
export const ApiKeyInput = document.querySelector<HTMLInputElement>(".apiKey")!;
export const ApiKeyInputParent = ApiKeyInput ? ApiKeyInput.closest('.textInput-wrapper') as HTMLElement : null;
export const sendButton = document.getElementById("send-button") as HTMLButtonElement;
export const ChatMessages = document.getElementById("chat-messages") as HTMLElement;
export const NewChat = document.getElementById("new-chat") as HTMLElement;
export const FreeUsage = document.getElementById("FreeUsage") as HTMLInputElement | null;
export const FreeUsageText = document.getElementById("FreeUsageText") as HTMLElement | null;
export const LanguageSelector = document.getElementById("output-language") as HTMLSelectElement;
const StatusWrapper = document.querySelector<HTMLElement>('.status-wrapper')!;
const Spinner = document.querySelector<HTMLElement>('.spinner')!;
const StatusText = document.querySelector<HTMLElement>('.status-text')!;

export function showSpinner(): void {
    StatusWrapper.classList.remove('hidden');
    Spinner.classList.remove('hidden');
    StatusText.classList.add('hidden');
    StatusText.textContent = '';
}

export function showStatus(msg: string): void {
    StatusWrapper.classList.remove('hidden');
    StatusText.classList.remove('hidden');
    StatusText.textContent = msg;
    Spinner.classList.add('hidden');
}

export function hideStatus(): void {
    StatusWrapper.classList.add('hidden');
    Spinner.classList.add('hidden');
    StatusText.classList.add('hidden');
}

export function renderMessage(role: string, content: string): void {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role === "assistant" ? "ai" : "user"}-message`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content; 
    
    messageDiv.appendChild(bubble);
    ChatMessages.appendChild(messageDiv);
    
    ChatMessages.scrollTop = ChatMessages.scrollHeight;
}

