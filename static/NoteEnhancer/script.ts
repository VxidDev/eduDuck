import { InitFileUploads } from "../Components/FileUploadHandler.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

// DOM Element Selections
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
const StatusWrapper = document.querySelector<HTMLElement>('.status-wrapper')!;
const Spinner = document.querySelector<HTMLElement>('.spinner')!;
const StatusText = document.querySelector<HTMLElement>('.status-text')!;

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

// Type Definitions
interface UsageData {
    remaining: number;
}

interface EnhanceNotesBody {
    notes: string;
    apiKey: string | null;
    model: string | null;
    language: string;
    apiMode: string;
    isFree: boolean;
}

interface EnhanceResponse {
    id: string;
}

interface UploadNotesResponse {
    notes: string;
}

interface ImportNotesResponse {
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
            if (FreeUsageText) {
                FreeUsageText.textContent = "Could not load usage data.";
            }
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

    // Note Enhancement Submit Handler
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

        // Validation
        if (!apiKey && !FreeUsage?.checked) {
            showStatus("Enter API key.");
            return;
        }
        if (!notes) {
            showStatus("Enter notes first.");
            return;
        }
        if (words.length > 2500) {
            showStatus("Notes too long.");
            return;
        }
        if (modelVisible && !model) {
            showStatus("Enter model.");
            return;
        }

        showSpinner();

        try {
            const body: EnhanceNotesBody = {
                notes,
                apiKey: FreeUsage?.checked ? null : apiKey,
                model: FreeUsage?.checked ? null : model,
                language: LanguageSelector.value.trim(),
                apiMode: FreeUsage?.checked ? "OpenAI" : APIModeSelector.value.trim(),
                isFree: FreeUsage?.checked ?? false
            };

            const res1 = await fetch("/note-enhancer/enhance", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });

            if (!res1.ok) {
                throw new Error(`HTTP error! status: ${res1.status}`);
            }

            const data: EnhanceResponse = await res1.json();
            window.location.href = `/note-enhancer/result?id=${encodeURIComponent(data.id)}`;

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
            console.error("Note enhancement error:", error);
            showStatus("Error while enhancing notes.");
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
            const LINEHEIGHT = 20;
            NoteInput.style.height = Math.min(
                NoteInput.scrollHeight,
                MAXLINES * LINEHEIGHT + 60
            ) + "px";

            hideStatus();
        } catch (error) {
            console.error("File upload error:", error);
            NoteInput.value = "File upload failed.";
            showStatus("File upload failed.");
        }
    }

    // Notes Import Handler
    async function ImportData(file: File): Promise<void> {
        const formData = new FormData();
        formData.append("noteFile", file);

        showSpinner();

        try {
            const res = await fetch("/note-enhancer/import-notes", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                showStatus("File upload failed.");
                return;
            }

            const data: ImportNotesResponse = await res.json();

            if (!data.err && data.id) {
                window.location.href = `/note-enhancer/result?id=${encodeURIComponent(data.id)}`;
            } else {
                showStatus(data.err || "Unknown error occurred.");
            }
        } catch (error) {
            console.error("Import error:", error);
            showStatus("Error importing notes.");
        }
    }

    // Initialize File Upload Handlers
    InitFileUploads({
        onRegularFile: SendFile,
        onImportFile: ImportData
    });
})();
