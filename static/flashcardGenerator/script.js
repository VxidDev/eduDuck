import { ValidateInput } from "../Components/ValidateInput.js";
import { CustomModelListeners } from "../Components/ModelSelector.js"
import { InitFileUploads } from "../Components/FileUploadHandler.js";
import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

const NoteInput = document.querySelector(".notes");
const Submit = document.querySelector(".submit");
const StatusLabel = document.querySelector(".status");
const TextInputs = document.querySelectorAll(".textInput");
const ApiKeyInput = document.querySelector(".apiKey");
const CustomModel = document.getElementById("customModel");
const CustomModelInput = document.querySelector(".customModelInput");
const LanguageSelector = document.getElementById("language");
const APIModeSelector = document.getElementById("apiMode");
const AmountSelector = document.getElementById("questionCount");
const CustomModelSelector = document.querySelector(".customModelSelector");
const FreeUsage = document.getElementById("FreeUsage");
const FreeUsageText = document.getElementById("FreeUsageText");

let FreeUsageLeft = 0;

StatusLabel.textContent = '';

CustomModelListeners();
( async () => { 

await GetFreeLimitUsage();

// Initial Fetch
if (FreeUsageText) {
	const request = await fetch('/get-usage' , {
		method: "GET",
		headers: { "Content-Type": "application/json" }
	});

	let usageData = await request.json();

	FreeUsageLeft = usageData.remaining || 0;
	if (FreeUsageLeft <= 0 && FreeUsage?.checked) Submit.disabled = true;
	FreeUsageText.textContent = `Welcome, ${window.CURRENT_USERNAME}! You have ${FreeUsageLeft} free uses today.`;
}
//

function getMaxLines(el) {
	const b = el.classList;
	return b.contains("slim") ? 1 : b.contains("standard") ? 5 : b.contains("large") ? 20 : 1;
}

TextInputs.forEach(ti => {
	const MAXLINES = getMaxLines(ti);
	const LINEHEIGHT = 25;
	ti.addEventListener("input", function () {
		this.style.height = "auto";
		this.style.height = Math.min(this.scrollHeight, MAXLINES * LINEHEIGHT + 35) + "px";
	});
});

Submit.addEventListener("click", async () => {
	if (FreeUsage && FreeUsage?.checked && FreeUsageLeft <= 0) {
		StatusLabel.textContent = "No free uses left today.";
		return;
	}

	StatusLabel.textContent = "";

	const notes = NoteInput.value.trim();
	const apiKey = ApiKeyInput.value.trim();
	const modelVisible = !CustomModelInput.classList.contains("hidden");
	const model = modelVisible ? CustomModelInput.value.trim() : null;
	const requiresApiKey = !FreeUsage || !FreeUsage.checked;

	ValidateInput(
		notes,
		apiKey,
		modelVisible,
		model,
		StatusLabel,
		notes.split(" "),
		requiresApiKey
	);

	if (!notes || !apiKey && requiresApiKey || notes.split(" ").length > 2500 || (!model && CustomModel.checked)) {
		console.error("[ DEBUG ] Didn't pass check...");
		return;
	}

	try {
		const body = {
			notes,
			apiKey: FreeUsage && FreeUsage.checked ? null : apiKey,
			model: FreeUsage && FreeUsage.checked ? null : model,
			language: LanguageSelector.value.trim(),
			apiMode: FreeUsage && FreeUsage.checked ? "OpenAI" : APIModeSelector.value.trim(),
			isFree: FreeUsage && FreeUsage.checked,
			amount: AmountSelector.value.trim()
		};

		const res1 = await fetch("/flashcard-generator/generate", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(body)
		});
		const data = await res1.json();

		window.location.href = `/flashcard-generator/result?id=${encodeURIComponent(data.id)}`;

		if (FreeUsageText && FreeUsage?.checked) { // If user somehow stays on page
			const request = await fetch('/get-usage' , {
				method: "GET",
				headers: { "Content-Type": "application/json" }
			});

			const usageData = await request.json();
			FreeUsageLeft = usageData.remaining || 0;
			FreeUsageText.textContent = `Welcome, ${window.CURRENT_USERNAME}! You have ${FreeUsageLeft} free uses today.`;

			if (FreeUsageLeft <= 0) Submit.disabled = true; 
		}

	} catch {
		StatusLabel.textContent = "Error while generating flashcards.";
	}
});

async function SendFile(file) {
	const formData = new FormData();
	formData.append("notesFile", file);

	NoteInput.textContent = "Loading...";

	const res = await fetch("/upload-notes", { method: "POST", body: formData });

	if (!res.ok) {
		NoteInput.textContent = "File upload failed.";
		return;
	}

	const data = await res.json();
	NoteInput.textContent = data.notes;

	const MAXLINES = getMaxLines(NoteInput);
	const LINEHEIGHT = 20;
	NoteInput.style.height = Math.min(
		NoteInput.scrollHeight,
		MAXLINES * LINEHEIGHT + 60
	) + "px";
}

async function ImportData(file) {
	const formData = new FormData();
	formData.append("flashcardFile", file);

	StatusLabel.textContent = "Loading...";

	const res = await fetch("/flashcard-generator/import-flashcards", {
		method: "POST",
		body: formData
	});

	if (!res.ok) {
		StatusLabel.textContent = "File upload failed.";
		return;
	}

	const data = await res.json();

	if (!data.err) {
		window.location.href = `/flashcard-generator/result?id=${encodeURIComponent(data.id)}`;
    } else {
		StatusLabel.textContent = data.err;
	}
}

InitFileUploads({
	onRegularFile: SendFile,
	onImportFile: ImportData
});
})();
