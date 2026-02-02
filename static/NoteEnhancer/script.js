import { InitFileUploads } from "../Components/FileUploadHandler.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";
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

const getMaxLines = el =>
	el.classList.contains("slim")
		? 1
		: el.classList.contains("standard")
		? 5
		: el.classList.contains("large")
		? 20
		: 1;

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

	const notes  = NoteInput.value.trim();
	const apiKey = ApiKeyInput.value.trim();
	const modelVisible = !CustomModelInput.classList.contains("hidden");
	const model  = modelVisible ? CustomModelInput.value.trim() : null;
	const words  = notes.split(" ");
	const requiresApiKey = !FreeUsage || !FreeUsage.checked;

	let msg =
		!apiKey && requiresApiKey
			? "Enter API key."
			: !notes
			? "Enter notes first."
			: words.length > 2500
			? "Notes too long."
			: modelVisible && !model
			? "Enter model."
			: "Generating...";

	StatusLabel.textContent = msg;
	if (!notes || !apiKey && requiresApiKey || words.length > 2500 || (!model && CustomModel.checked)) return;

	try {
		const body = {
			notes,
			apiKey: FreeUsage && FreeUsage.checked ? null : apiKey,
			model: FreeUsage && FreeUsage.checked ? null : model,
			language: LanguageSelector.value.trim(),
			apiMode: FreeUsage && FreeUsage.checked ? "OpenAI" : APIModeSelector.value.trim(),
			isFree: FreeUsage && FreeUsage.checked
		};

		const res1 = await fetch("/note-enhancer/enhance", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(body)
		});

		const data = await res1.json();

		window.location.href = `/note-enhancer/result?id=${encodeURIComponent(data.id)}`;

		if (FreeUsageText && FreeUsage && FreeUsage?.checked) { // If user somehow stays on page
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
		StatusLabel.textContent = "Error while enhancing notes.";
	}
});

async function SendFile(file) {
	const formData = new FormData();
	formData.append("notesFile", file);

	NoteInput.textContent = "Loading...";

	const res = await fetch("/upload-notes", {
		method: "POST",
		body: formData
	});

	if (!res.ok) {
		NoteInput.textContent = "File upload failed.";
		return;
	}

	const data = await res.json();
	NoteInput.textContent = data.notes;

	const MAXLINES   = getMaxLines(NoteInput);
	const LINEHEIGHT = 20;
	NoteInput.style.height = Math.min(
		NoteInput.scrollHeight,
		MAXLINES * LINEHEIGHT + 60
	) + "px";
}

async function ImportData(file) {
	const formData = new FormData();
	formData.append("noteFile", file);

	StatusLabel.textContent = "Loading...";

	const res = await fetch("/note-enhancer/import-notes", {
		method: "POST",
		body: formData
	});

	if (!res.ok) {
		StatusLabel.textContent = "File upload failed.";
		return;
	}

	const data = await res.json();

	if (!data.err) {
		window.location.href = `/note-enhancer/result?id=${encodeURIComponent(data.id)}`;
    } else {
		StatusLabel.textContent = data.err
	}
}

InitFileUploads({
	onRegularFile: SendFile,
	onImportFile: ImportData
})

})();
