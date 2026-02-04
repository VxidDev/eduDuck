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

const StartDateInput = document.getElementById("startDate") as HTMLInputElement;
const EndDateInput = document.getElementById("endDate") as HTMLInputElement;
const HoursInput = document.getElementById("hoursPerDay") as HTMLInputElement;
const LearningStyleInputs = document.querySelectorAll<HTMLInputElement>(".learningStyle");
const GoalInput = document.getElementById("studyGoal") as HTMLInputElement;

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

interface StudyPlanBody {
    notes: string;
    apiKey: string | null;
    model: string | null;
    language: string;
    apiMode: string;
    isFree: boolean;
    startDate: string;
    endDate: string;
    hoursPerDay: string;
    learningStyles: string[];
    goal: string;
}

interface StudyPlanResponse {
    id: string;
}

interface UploadNotesResponse {
    notes: string;
}

interface ImportPlanResponse {
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

    // Study Plan Generation Submit Handler
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

        const startDate = StartDateInput.value;
        const endDate = EndDateInput.value;
        const hoursPerDay = HoursInput.value;
        const learningStyles = Array.from(LearningStyleInputs).filter(c => c.checked).map(c => c.value);
        const goal = GoalInput.value.trim();

        // Validation with spinner/status feedback
        if (!apiKey && requiresApiKey) {
            showStatus("Enter API key.");
            return;
        }
        if (!notes) {
            showStatus("Enter topics/notes first.");
            return;
        }
        if (words.length > 2500) {
            showStatus("Notes too long.");
            return;
        }
        if (!startDate || !endDate) {
            showStatus("Select start and end date.");
            return;
        }
        if (learningStyles.length === 0) {
            showStatus("Select at least one learning style.");
            return;
        }
        if (modelVisible && !model) {
            showStatus("Enter model.");
            return;
        }
        if (!goal) {
            showStatus("Enter goal first.");
            return;
        }

        showSpinner();

        try {
            const body: StudyPlanBody = {
                notes,
                apiKey: FreeUsage?.checked ? null : apiKey,
                model: FreeUsage?.checked ? null : model,
                language: LanguageSelector?.value?.trim() || "eng",
                apiMode: FreeUsage?.checked ? "OpenAI" : APIModeSelector.value.trim(),
                isFree: FreeUsage?.checked ?? false,
                startDate,
                endDate,
                hoursPerDay,
                learningStyles,
                goal
            };

            const res1 = await fetch("/study-plan-generator/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });

            if (!res1.ok) {
                throw new Error(`HTTP error! status: ${res1.status}`);
            }

            const data: StudyPlanResponse = await res1.json();
            window.location.href = `/study-plan-generator/result?plan=${encodeURIComponent(data.id)}`;

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
            console.error("Study plan generation error:", error);
            showStatus("Error while generating study plan.");
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

    // Study Plan Import Handler
    async function ImportData(file: File): Promise<void> {
        const formData = new FormData();
        formData.append("planFile", file);

        showSpinner();

        try {
            const res = await fetch("/study-plan-generator/import-plan", {
                method: "POST",
                body: formData
            });

            if (!res.ok) {
                showStatus("File upload failed.");
                return;
            }

            const data: ImportPlanResponse = await res.json();

            if (!data.err && data.id) {
                window.location.href = `/study-plan-generator/result?plan=${encodeURIComponent(data.id)}`;
            } else {
                showStatus(data.err || "Unknown error occurred.");
            }
        } catch (error) {
            console.error("Import error:", error);
            showStatus("Error importing study plan.");
        }
    }

    // Initialize File Upload Handlers
    InitFileUploads({
        onRegularFile: SendFile,
        onImportFile: ImportData
    });
})();
