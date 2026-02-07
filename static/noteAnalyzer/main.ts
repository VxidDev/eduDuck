import { InitFileUploads } from "../Components/FileUploadHandler.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";


// DOM Element Selections with proper TypeScript types
const NoteInput = document.querySelector<HTMLTextAreaElement>(".notes")!;
const Submit = document.querySelector<HTMLButtonElement>(".submit")!;
const TextInputs = document.querySelectorAll<HTMLTextAreaElement>(".textInput");
const ApiKeyInput = document.querySelector<HTMLInputElement>(".apiKey")!;
const CustomModel = document.getElementById("customModel") as HTMLInputElement;
const CustomModelInput = document.querySelector<HTMLInputElement>(".customModelInput")!;
const LanguageSelector = document.getElementById("language") as HTMLSelectElement;
const APIModeSelector = document.getElementById("apiMode") as HTMLSelectElement;
const FreeUsage = document.getElementById("FreeUsage") as HTMLInputElement | null;
const FreeUsageText = document.getElementById("FreeUsageText") as HTMLElement | null;


// Spinner elements
const StatusWrapper = document.querySelector<HTMLElement>('.status-wrapper')!;
const Spinner = document.querySelector<HTMLElement>('.spinner')!;
const StatusText = document.querySelector<HTMLElement>('.status-text')!;


// Spinner Management Functions
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


// State
let FreeUsageLeft: number = 0;


// Initialize Custom Model Listeners
CustomModelListeners();


// Main IIFE
(async (): Promise<void> => {
    await GetFreeLimitUsage();


    // Initial Free Usage Fetch
    if (FreeUsageText) {
        try {
            const request = await fetch('/get-usage', {
                method: "GET",
                headers: { "Content-Type": "application/json" }
            });


            const usageData: UsageData = await request.json();


            FreeUsageLeft = usageData.remaining || 0;
            if (FreeUsageLeft <= 0 && FreeUsage?.checked) {
                Submit.disabled = true;
            }
            FreeUsageText.textContent = `${FreeUsageLeft} free uses remaining today.`;
        } catch (error) {
            console.error("Error fetching usage data:", error);
            FreeUsageText.textContent = "Could not load usage data.";
        }
    }


    // Auto-resize Text Inputs
    const getMaxLines = (el: HTMLTextAreaElement): number =>
        el.classList.contains("slim")
            ? 1
            : el.classList.contains("standard")
            ? 5
            : el.classList.contains("large")
            ? 20
            : 1;


    TextInputs.forEach((ti) => {
        const MAXLINES = getMaxLines(ti);
        const LINEHEIGHT = 25;


        ti.addEventListener("input", function (this: HTMLTextAreaElement): void {
            this.style.height = "auto";
            this.style.height = Math.min(this.scrollHeight, MAXLINES * LINEHEIGHT + 35) + "px";
        });
    });


    // Note Analysis Submit Handler
    Submit.addEventListener("click", async (): Promise<void> => {
        if (FreeUsage?.checked && FreeUsageLeft <= 0) {
            showStatus("No free uses left today.");
            return;
        }


        hideStatus();


        const notes = NoteInput.value.trim();
        const apiKey = ApiKeyInput.value.trim();
        const modelVisible = !CustomModelInput.classList.contains("hidden");
        const model = modelVisible ? CustomModelInput.value.trim() : null;
        const words = notes.split(" ");
        const requiresApiKey = !FreeUsage || !FreeUsage.checked;


        // Validation with spinner/status feedback
        if (!apiKey && requiresApiKey) {
            showStatus("Enter API key.");
            return;
        }
        if (!notes) {
            showStatus("Enter notes first.");
            return;
        }
        if (words.length > 2500) {
            showStatus("Notes too long (max 2500 words).");
            return;
        }
        if (modelVisible && !model) {
            showStatus("Enter model.");
            return;
        }


        showSpinner();


        try {
            const body: NoteAnalysisBody = {
                notes,
                apiKey: FreeUsage?.checked ? null : apiKey,
                model: FreeUsage?.checked ? null : model,
                language: LanguageSelector?.value?.trim() || "English",
                apiMode: FreeUsage?.checked ? "OpenAI" : APIModeSelector.value.trim(),
                isFree: FreeUsage?.checked ?? false,
                temperature: 0.3,
                top_p: 0.9
            };


            const res1 = await fetch("/note-analyzer/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });


            if (!res1.ok) {
                throw new Error(`HTTP error! status: ${res1.status}`);
            }


            const data: NoteAnalysisResponse = await res1.json();


            // Check if response contains an error message
            if (data.analysis) {
                showStatus(data.analysis);
                return;
            }


            if (data.id) {
                window.location.href = `/note-analyzer/result?id=${encodeURIComponent(data.id)}`;
            } else {
                showStatus("Error: No analysis ID returned.");
            }


            // Update free usage if user somehow stays on page
            if (FreeUsageText && FreeUsage?.checked) {
                const request = await fetch('/get-usage', {
                    method: "GET",
                    headers: { "Content-Type": "application/json" }
                });


                const usageData: UsageData = await request.json();
                FreeUsageLeft = usageData.remaining || 0;


                if (FreeUsageLeft <= 0) {
                    Submit.disabled = true;
                }
                FreeUsageText.textContent = `${FreeUsageLeft} free uses remaining today.`;
            }


        } catch (error) {
            console.error("Note analysis error:", error);
            showStatus("Error while analyzing notes.");
        }
    });


    // File Upload Handler for Notes
    async function SendFile(file: File): Promise<void> {
        const formData = new FormData();
        formData.append("notesFile", file);


        NoteInput.value = "Loading...";
        showSpinner();


        try {
            const res = await fetch("/upload-notes", {
                method: "POST",
                body: formData
            });


            if (!res.ok) {
                NoteInput.value = "File upload failed.";
                showStatus("File upload failed.");
                return;
            }


            const data: UploadNotesResponse = await res.json();
            NoteInput.value = data.notes;


            // Auto-resize textarea
            const MAXLINES = getMaxLines(NoteInput);
            const LINEHEIGHT = 25;
            NoteInput.style.height = Math.min(
                NoteInput.scrollHeight,
                MAXLINES * LINEHEIGHT + 35
            ) + "px";


            hideStatus();
        } catch (error) {
            console.error("File upload error:", error);
            NoteInput.value = "File upload failed.";
            showStatus("File upload failed.");
        }
    }


    // Note Analysis Import Handler
    async function ImportData(file: File): Promise<void> {
        const formData = new FormData();
        formData.append("analysisFile", file);


        showSpinner();


        try {
            const res = await fetch("/note-analyzer/import-analysis", {
                method: "POST",
                body: formData
            });


            if (!res.ok) {
                showStatus("File upload failed.");
                return;
            }


            const data: ImportAnalysisResponse = await res.json();


            if (!data.err && data.id) {
                window.location.href = `/note-analyzer/result?id=${encodeURIComponent(data.id)}`;
            } else {
                showStatus(data.err || "Unknown error occurred.");
            }
        } catch (error) {
            console.error("Import error:", error);
            showStatus("Error importing note analysis.");
        }
    }


    // Initialize File Upload Handlers
    InitFileUploads({
        onRegularFile: SendFile,
        onImportFile: ImportData
    });
})();