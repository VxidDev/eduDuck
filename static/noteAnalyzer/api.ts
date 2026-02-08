import { FreeUsageText } from "./ui.js";

// Type Definitions
interface UsageData {
    remaining: number;
}

interface NoteAnalysisBody {
    notes: string;
    apiKey: string | null;
    model: string | null;
    language: string;
    apiMode: string;
    isFree: boolean;
    temperature?: number;
    top_p?: number;
}

interface NoteAnalysisResponse {
    id?: string;
    analysis?: string;
}

interface UploadNotesResponse {
    notes: string;
}

interface ImportAnalysisResponse {
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

export async function analyzeNotes(body: NoteAnalysisBody): Promise<NoteAnalysisResponse> {
    const res = await fetch("/note-analyzer/analyze", {
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

export async function importAnalysis(file: File): Promise<ImportAnalysisResponse> {
    const formData = new FormData();
    formData.append("analysisFile", file);

    const res = await fetch("/note-analyzer/import-analysis", {
        method: "POST",
        body: formData
    });

    if (!res.ok) {
        throw new Error("File upload failed.");
    }

    return await res.json();
}
