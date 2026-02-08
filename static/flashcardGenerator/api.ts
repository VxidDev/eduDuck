import { FreeUsageText } from "./ui.js";

// Type Definitions
interface UsageData {
    remaining: number;
}

interface FlashcardGenerationBody {
    notes: string;
    apiKey: string | null;
    model: string | null;
    language: string;
    apiMode: string;
    isFree: boolean;
    amount: string;
}

interface FlashcardResponse {
    id: string;
}

interface UploadNotesResponse {
    notes: string;
}

interface ImportFlashcardsResponse {
    id?: string;
    err?: string;
}

export async function getFreeLimitUsage(): Promise<number> {
    if (!FreeUsageText) return 0;
    try {
        const request = await fetch('/get-usage', {
            method: "GET",
            headers: { "Content-Type": "application/json" }
        });

        const usageData: UsageData = await request.json();
        const remaining = usageData.remaining || 0;
        FreeUsageText.textContent = `${remaining} free uses remaining today.`;
        return remaining;
    } catch (error) {
        console.error("Error fetching usage data:", error);
        if (FreeUsageText) {
            FreeUsageText.textContent = "Could not load usage data.";
        }
        return 0;
    }
}

export async function generateFlashcards(body: FlashcardGenerationBody): Promise<FlashcardResponse> {
    const res = await fetch("/flashcard-generator/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
    });

    if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
    }

    return await res.json();
}

export async function uploadNotes(file: File): Promise<UploadNotesResponse> {
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

export async function importFlashcards(file: File): Promise<ImportFlashcardsResponse> {
    const formData = new FormData();
    formData.append("flashcardFile", file);

    const res = await fetch("/flashcard-generator/import-flashcards", {
        method: "POST",
        body: formData
    });

    if (!res.ok) {
        throw new Error("File upload failed.");
    }

    return await res.json();
}
