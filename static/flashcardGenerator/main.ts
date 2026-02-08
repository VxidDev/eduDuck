import { ValidateInput } from "../Components/ValidateInput.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
import { InitFileUploads } from "../Components/FileUploadHandler.js";
import { showSpinner, showStatus, hideStatus } from "../Components/StatusManager.js";
import {
    NoteInput, Submit, TextInputs, ApiKeyInput, CustomModel, CustomModelInput,
    LanguageSelector, APIModeSelector, AmountSelector, FreeUsage, FreeUsageText, ApiKeyInputParent
} from "./ui.js";
import { getFreeLimitUsage, generateFlashcards, uploadNotes, importFlashcards } from "./api.js";

let FreeUsageLeft = 0;

CustomModelListeners();

const getMaxLines = (el: HTMLTextAreaElement): number => {
    const b = el.classList;
    return b.contains("slim") ? 1 : b.contains("standard") ? 5 : b.contains("large") ? 20 : 1;
};

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
        const data = await importFlashcards(file);

        if (!data.err && data.id) {
            window.location.href = `/flashcard-generator/result?id=${encodeURIComponent(data.id)}`;
        } else {
            showStatus(data.err || "Unknown error occurred.");
        }
    } catch (error) {
        console.error("Import error:", error);
        showStatus("Error importing flashcards.");
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
        const requiresApiKey = !FreeUsage || !FreeUsage.checked;
        const words = notes.split(" ");

        ValidateInput(
            notes,
            apiKey,
            modelVisible,
            model,
            document.querySelector<HTMLElement>('.status-text')!,
            words.length,
            requiresApiKey
        );

        if (!notes || (!apiKey && requiresApiKey) || words.length > 2500 || (!model && CustomModel.checked)) {
            return;
        }

        showSpinner();

        try {
            const body = {
                notes,
                apiKey: FreeUsage?.checked ? null : apiKey,
                model: FreeUsage?.checked ? null : model,
                language: LanguageSelector.value.trim(),
                apiMode: FreeUsage?.checked ? "OpenAI" : APIModeSelector.value.trim(),
                isFree: FreeUsage?.checked ?? false,
                amount: AmountSelector.value.trim()
            };

            const data = await generateFlashcards(body);
            window.location.href = `/flashcard-generator/result?id=${encodeURIComponent(data.id)}`;

            if (FreeUsageText && FreeUsage?.checked) {
                FreeUsageLeft = await getFreeLimitUsage();
                if (FreeUsageLeft <= 0) {
                    Submit.disabled = true;
                }
            }

        } catch (error) {
            console.error("Flashcard generation error:", error);
            showStatus("Error while generating flashcards.");
        }
    });

    InitFileUploads({
        onRegularFile: handleFileUpload,
        onImportFile: handleImport
    });
});
