import { autoResize } from "../Components/AutoResize.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import {
    CustomModel, CustomModelInput, APIModeSelector, UserInput, ApiKeyInput,
    sendButton, NewChat, FreeUsage, showSpinner, showStatus, hideStatus, renderMessage, ApiKeyInputParent, LanguageSelector
} from "./ui.js";
import { getFreeLimitUsage, generate, storeConversation, uploadFile } from "./api.js";
import { addMessage, getHistory, parseInitialChat } from "./chat.js";

let FreeUsageLeft = 0;
let CurrentDuckAIQueryID: string | null = null;

sendButton.disabled = true;
CustomModelListeners();

function updateSendButton(): void {
    const hasText = UserInput.value.trim();
    const usageOk = !FreeUsage?.checked || FreeUsageLeft > 0;
    sendButton.disabled = !hasText || !usageOk;
}

async function initialize(): Promise<void> {
    FreeUsageLeft = await getFreeLimitUsage();
    updateSendButton();

    const mainContent = document.querySelector(".main-content") as HTMLElement;
    const initialChatData = mainContent?.dataset.chat;

    if (initialChatData) {
        parseInitialChat(initialChatData);
        mainContent.dataset.chat = '';

        const urlParams = new URLSearchParams(window.location.search);
        CurrentDuckAIQueryID = urlParams.get("id");
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    await initialize();

    UserInput.addEventListener("input", () => {
        autoResize(UserInput);
        updateSendButton();
    });

    // Toggle API Key input visibility
    if (FreeUsage && ApiKeyInputParent) { // Add null check for ApiKeyInputParent here
        FreeUsage.addEventListener('change', () => {
            if (FreeUsage && ApiKeyInputParent) { // Add null check for ApiKeyInputParent here
                if (FreeUsage.checked) {
                    ApiKeyInputParent.classList.add('hidden');
                } else {
                    ApiKeyInputParent.classList.remove('hidden');
                }
            }
        });
        // Set initial state
        if (FreeUsage.checked) {
            ApiKeyInputParent.classList.add('hidden');
        }
    }

    sendButton.addEventListener("click", async (): Promise<void> => {
        if (FreeUsage?.checked && FreeUsageLeft <= 0) {
            showStatus("No free uses left today.");
            updateSendButton();
            return;
        }

        hideStatus();
        sendButton.disabled = true;

        const text = UserInput.value.trim();
        const apiKey = ApiKeyInput.value.trim();
        const useCustomModel = !CustomModelInput.classList.contains("hidden") && CustomModel.checked;
        const modelValue = CustomModelInput.value.trim();
        const requiresApiKey = !FreeUsage?.checked;

        if (!text) {
            showStatus("Please enter a message.");
            updateSendButton();
            return;
        }

        if (requiresApiKey && !apiKey) {
            showStatus("Please enter your API key.");
            updateSendButton();
            return;
        }

        if (text.split(" ").length > 2500) {
            showStatus("Message is too long (max 2500 words).");
            updateSendButton();
            return;
        }

        if (useCustomModel && !modelValue) {
            showStatus("Please enter a custom model.");
            updateSendButton();
            return;
        }

        addMessage("user", text);
        renderMessage("user", text);
        UserInput.value = "";
        updateSendButton();

        const history = getHistory();
        const model = useCustomModel ? modelValue : null;

        showSpinner();

        try {
            const botMessage = await generate(
                history,
                FreeUsage?.checked ? null : apiKey,
                FreeUsage?.checked ? null : model,
                FreeUsage?.checked ? "OpenAI" : APIModeSelector.value.trim(),
                FreeUsage?.checked ?? false,
                LanguageSelector.value.trim()
            );

            addMessage("assistant", botMessage);
            renderMessage("assistant", botMessage);
            hideStatus();

            const queryID = await storeConversation(
                [{ role: "user", content: text }, { role: "assistant", content: botMessage }],
                CurrentDuckAIQueryID
            );

            if (queryID && !CurrentDuckAIQueryID) {
                CurrentDuckAIQueryID = queryID;
                window.history.pushState({}, "", `/duck-ai?id=${queryID}`);
            }

            if (FreeUsage?.checked) {
                FreeUsageLeft = await getFreeLimitUsage();
                updateSendButton();
            }

        } catch {
            showStatus("Error while generating response.");
        } finally {
            updateSendButton();
        }
    });

    document.getElementById("fileInput")?.addEventListener("change", async function (this: HTMLInputElement) {
        const wrapper = this.closest('.file-upload-wrapper');
        const display = wrapper?.querySelector('.fileButton') as HTMLElement;

        if (!display || !this.files || !this.files.length) return;

        const file = this.files[0];
        const names = Array.from(this.files).map(f => f.name).join(', ');
        display.textContent = names.length > 30 ? `${names.slice(0, 27)}...` : names;
        display.classList.add('has-file');

        showSpinner();
        const notes = await uploadFile(file);
        hideStatus();

        if (notes) {
            UserInput.value = notes;
            autoResize(UserInput);
            updateSendButton();
        } else {
            showStatus("File upload failed.");
        }
    });

    NewChat.addEventListener("click", () => window.location.href = "/duck-ai");

    autoResize(UserInput);
});
