import { InitFileUploads } from "../Components/FileUploadHandler.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import { showSpinner, showStatus, hideStatus } from "../Components/StatusManager.js";
import {
    NoteInput, Submit, TextInputs, ApiKeyInput, CustomModel, CustomModelInput,
    LanguageSelector, APIModeSelector, FreeUsage, FreeUsageText, StartDateInput,
    EndDateInput, HoursInput, LearningStyleInputs, GoalInput, ApiKeyInputParent
} from "./ui.js";
import { getFreeLimitUsage, generateStudyPlan, uploadNotes, importPlan } from "./api.js";

let FreeUsageLeft = 0;

CustomModelListeners();

const getMaxLines = (el: HTMLTextAreaElement): number =>
    el.classList.contains("slim")
        ? 1
        : el.classList.contains("standard")
        ? 5
        : el.classList.contains("large")
        ? 20
        : 1;

async function handleFileUpload(file: File) {
    NoteInput.value = "Loading...";
    showSpinner();

    try {
        const data = await uploadNotes(file);
        NoteInput.value = data.notes;

        const MAXLINES = getMaxLines(NoteInput);
        const LINEHEIGHT = 20;
        NoteInput.style.height = `${Math.min(
            NoteInput.scrollHeight,
            MAXLINES * LINEHEIGHT + 60
        )}px`;

        hideStatus();
    } catch (error) {
            console.error("File upload error:", error);
        NoteInput.value = "File upload failed.";
        showStatus("File upload failed.");
    }
}

async function handleImport(file: File) {
    showSpinner();

    try {
        const data = await importPlan(file);

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

document.addEventListener('DOMContentLoaded', async () => {
    FreeUsageLeft = await getFreeLimitUsage();
    if (FreeUsageLeft <= 0 && FreeUsage?.checked) {
        Submit.disabled = true;
    }

    TextInputs.forEach((ti) => {
        const MAXLINES = getMaxLines(ti);
        const LINEHEIGHT = 25;

        ti.addEventListener("input", function (this: HTMLTextAreaElement): void {
            this.style.height = "auto";
            this.style.height = `${Math.min(this.scrollHeight, MAXLINES * LINEHEIGHT + 35)}px`;
        });
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

    Submit.addEventListener("click", async () => {
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
            const body = {
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

            const data = await generateStudyPlan(body);
            window.location.href = `/study-plan-generator/result?plan=${encodeURIComponent(data.id)}`;

            if (FreeUsageText && FreeUsage?.checked) {
                FreeUsageLeft = await getFreeLimitUsage();
                if (FreeUsageLeft <= 0) {
                    Submit.disabled = true;
                }
            }

        } catch (error) {
            console.error("Study plan generation error:", error);
            showStatus("Error while generating study plan.");
        }
    });

    InitFileUploads({
        onRegularFile: handleFileUpload,
        onImportFile: handleImport
    });
});
