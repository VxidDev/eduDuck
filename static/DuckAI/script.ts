import { ValidateInput } from "../Components/ValidateInput.js";
import { autoResize } from "../Components/AutoResize.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";


const CustomModel = document.getElementById("customModel") as HTMLInputElement;
const CustomModelInput = document.querySelector<HTMLInputElement>(".customModelInput")!;
const APIModeSelector = document.getElementById("apiMode") as HTMLSelectElement;
const UserInput = document.getElementById("user-input") as HTMLTextAreaElement;
const ApiKeyInput = document.querySelector<HTMLInputElement>(".apiKey")!;
const sendButton = document.getElementById("send-button") as HTMLButtonElement;
const ChatMessages = document.getElementById("chat-messages") as HTMLElement;
const NewChat = document.getElementById("new-chat") as HTMLElement;
const FreeUsage = document.getElementById("FreeUsage") as HTMLInputElement | null;
const FreeUsageText = document.getElementById("FreeUsageText") as HTMLElement | null;
const StatusWrapper = document.querySelector<HTMLElement>('.status-wrapper')!;
const Spinner = document.querySelector<HTMLElement>('.spinner')!;
const StatusText = document.querySelector<HTMLElement>('.status-text')!;


let FreeUsageLeft: number = 0;
let Messages: Array<{ role: string; content: string }> = [];


// Spinner and Status Management Functions
function showSpinner(): void {
    StatusWrapper.classList.remove('hidden');
    Spinner.classList.remove('hidden');
    StatusText.classList.add('hidden');
    StatusText.textContent = '';
}


function showStatus(msg: string): void {
    StatusWrapper.classList.remove('hidden');
    StatusText.classList.remove('hidden');
    StatusText.textContent = msg;
    Spinner.classList.add('hidden');
}


function hideStatus(): void {
    StatusWrapper.classList.add('hidden');
    Spinner.classList.add('hidden');
    StatusText.classList.add('hidden');
}


sendButton.disabled = true;
CustomModelListeners();


(async (): Promise<void> => { 
    if (FreeUsageText) await GetFreeLimitUsage();


    // Initial Fetch
    if (FreeUsageText) {
        const request = await fetch('/get-usage', {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });


        let usageData = await request.json();


        FreeUsageLeft = usageData.remaining || 0;
        if (FreeUsageLeft <= 0 && FreeUsage?.checked) sendButton.disabled = true;
    }


    // Initial Chat Parse If ID in DB and user is logged in
    const mainContent = document.querySelector(".main-content") as HTMLElement;
    const initialChatData = mainContent?.dataset.chat;


    if (initialChatData && initialChatData !== "" && initialChatData !== "null") {
        try {
            const parsedChat = JSON.parse(initialChatData);
            parsedChat.forEach((msg: { role: string; content: string }) => {
                Messages.push(msg);
                ChatMessages.innerHTML += `
                    <div class="message ${msg.role === "assistant" ? "ai" : "user"}-message">
                        <div class="message-bubble">${msg.content}</div>
                    </div>`;
            });

            const urlParams = new URLSearchParams(window.location.search);
            const queryID = urlParams.get("id");
            if (parsedChat.length !== 0 && queryID) {
                (window as any).CurrentDuckAIQueryID = queryID;
            }

            ChatMessages.scrollTop = ChatMessages.scrollHeight;
            mainContent.dataset.chat = '';
        } catch (err) {
            console.error("Failed to parse initial DuckAI chat:", err);
        }
    }


    function updateSendButton(): void {
        const hasText = UserInput.value.trim();
        const usageOk = !FreeUsage?.checked || FreeUsageLeft > 0;
        sendButton.disabled = !hasText || !usageOk;
    }


    UserInput.addEventListener("input", () => {
        autoResize(UserInput);
        updateSendButton();
    });


    sendButton.addEventListener("click", async (): Promise<void> => {
        if (FreeUsage && FreeUsage?.checked && FreeUsageLeft <= 0) {
            showStatus("No free uses left today.");
            updateSendButton();
            return;
        }


        hideStatus();
        sendButton.disabled = true;


        const text = UserInput.value.trim();
        const words = text.split(" ");
        const apiKey = ApiKeyInput.value.trim();
        const useCustomModel = !CustomModelInput.classList.contains("hidden") && CustomModel.checked;
        const modelValue = CustomModelInput.value.trim();
        const requiresApiKey = !FreeUsage || !FreeUsage.checked;


        if (!text) {
            showStatus("Please enter a message.");
            updateSendButton();
            return;
        }

        if (!apiKey && requiresApiKey) {
            showStatus("Please enter your API key.");
            updateSendButton();
            return;
        }

        if (words.length > 2500) {
            showStatus("Message is too long (max 2500 words).");
            updateSendButton();
            return;
        }

        if (useCustomModel && !modelValue) {
            showStatus("Please enter a custom model.");
            updateSendButton();
            return;
        }

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


        showSpinner();


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
            hideStatus();


            if ((window as any).CURRENT_USERNAME) {
                try {
                    const storeRes = await fetch("/duck-ai/store-conversation", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            messages: [
                                { role: "user", content: text },
                                { role: "assistant", content: botMessage }
                            ],
                            queryID: (window as any).CurrentDuckAIQueryID || null
                        })
                    });


                    if (storeRes.ok) {
                        const storeData = await storeRes.json();


                        if (storeData.queryID) {
                            if (!(window as any).CurrentDuckAIQueryID) {
                                (window as any).CurrentDuckAIQueryID = storeData.queryID;
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
                if (FreeUsageLeft <= 0) sendButton.disabled = true;
                FreeUsageText.textContent = `${FreeUsageLeft} free uses remaining today.`;
            }


        } catch {
            showStatus("Error while generating response.");
        } finally {
            updateSendButton();
        }
    });


    async function SendFile(file: File): Promise<void> {
        const formData = new FormData();
        formData.append("notesFile", file);


        showSpinner();


        const res = await fetch("/upload-notes", { method: "POST", body: formData });


        if (!res.ok) {
            showStatus("File upload failed.");
            return;
        }


        const data = await res.json();
        UserInput.value = data.notes;
        hideStatus();


        autoResize(UserInput);
        updateSendButton();
    }


    document.getElementById("fileInput")?.addEventListener("change", function (this: HTMLInputElement): void {
        const wrapper = this.closest('.file-upload-wrapper');
        const display = wrapper?.querySelector('.fileButton') as HTMLElement;


        if (!display) return;


        if (this.files && this.files.length) {
            const names = Array.from(this.files).map(f => f.name).join(', ');
            display.textContent = names.length > 30 ? `${names.slice(0, 27)}...` : names;
            display.classList.add('has-file');


            const file = this.files[0];
            SendFile(file);
        } else {
            display.textContent = (window as any).defaultText;
            display.classList.remove('has-file');
        }
    });


    NewChat.addEventListener("click", () => window.location.href = "/duck-ai");
    autoResize(UserInput);


})();
