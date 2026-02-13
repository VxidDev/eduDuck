import { FreeUsageText } from "./ui.js";
export async function getFreeLimitUsage() {
    if (!FreeUsageText)
        return 0;
    try {
        const request = await fetch("/get-usage", {
            method: "GET",
            headers: { "Content-Type": "application/json" },
        });
        if (!request.ok) {
            FreeUsageText.textContent = "Login to see usage";
            return 0;
        }
        const data = await request.json();
        const remaining = data.remaining || 0;
        FreeUsageText.textContent = `${remaining} free uses remaining today.`;
        return remaining;
    }
    catch (err) {
        FreeUsageText.textContent = "Error loading usage";
        console.error(err);
        return 0;
    }
}
export async function generate(history, apiKey, model, apiMode, isFree, language) {
    const res = await fetch("/duck-ai/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message: history,
            apiKey,
            model,
            apiMode,
            isFree,
            language
        })
    });
    const data = await res.json();
    return data.response.trim();
}
export async function storeConversation(messages, queryID) {
    if (!window.CURRENT_USERNAME)
        return null;
    try {
        const storeRes = await fetch("/duck-ai/store-conversation", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                messages,
                queryID
            })
        });
        if (storeRes.ok) {
            const storeData = await storeRes.json();
            return storeData.queryID || null;
        }
        else {
            console.error("DuckAI store failed:", storeRes.status, storeRes.statusText);
        }
    }
    catch (err) {
        console.error("DuckAI store conversation error:", err);
    }
    return null;
}
export async function uploadFile(file) {
    const formData = new FormData();
    formData.append("notesFile", file);
    const res = await fetch("/upload-notes", { method: "POST", body: formData });
    if (!res.ok) {
        return null;
    }
    const data = await res.json();
    return data.notes;
}
//# sourceMappingURL=api.js.map