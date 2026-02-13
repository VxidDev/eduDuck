import { FreeUsageText } from "./ui.js";
export async function getFreeLimitUsage() {
    if (!FreeUsageText)
        return 0;
    try {
        const request = await fetch('/get-usage', {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });
        const usageData = await request.json();
        const remaining = usageData.remaining || 0;
        FreeUsageText.textContent = `${remaining} free uses remaining today.`;
        return remaining;
    }
    catch (error) {
        console.error("Error fetching usage data:", error);
        if (FreeUsageText) {
            FreeUsageText.textContent = "Could not load usage data.";
        }
        return 0;
    }
}
export async function generateQuiz(body) {
    const res = await fetch("/quiz-generator/gen-quiz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });
    if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
    }
    return await res.json();
}
export async function uploadNotes(file) {
    const formData = new FormData();
    formData.append("notesFile", file);
    const res = await fetch("/upload-notes", {
        method: "POST",
        body: formData
    });
    if (!res.ok) {
        throw new Error("File upload failed.");
    }
    return await res.json();
}
export async function importQuiz(file) {
    const formData = new FormData();
    formData.append("quizFile", file);
    const res = await fetch("/quiz-generator/import-quiz", {
        method: "POST",
        body: formData
    });
    if (!res.ok) {
        throw new Error("File upload failed.");
    }
    return await res.json();
}
//# sourceMappingURL=api.js.map