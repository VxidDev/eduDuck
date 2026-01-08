import { InitFileUploads } from "../Components/FileUploadHandler.js";
import { CustomModelListeners } from "../Components/ModelSelector.js";

const NoteInput        = document.querySelector(".notes");
const Submit           = document.querySelector(".submit");
const StatusLabel      = document.querySelector(".status");
const TextInputs       = document.querySelectorAll(".textInput");
const ApiKeyInput      = document.querySelector(".apiKey");
const CustomModel      = document.getElementById("customModel");
const CustomModelInput = document.querySelector(".customModelInput");
const LanguageSelector = document.getElementById("language");
const APIModeSelector  = document.getElementById("apiMode");

StatusLabel.textContent = '';

CustomModelListeners();

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
	StatusLabel.textContent = "";

	const notes  = NoteInput.value.trim();
	const apiKey = ApiKeyInput.value.trim();
	const modelVisible = !CustomModelInput.classList.contains("hidden");
	const model  = modelVisible ? CustomModelInput.value.trim() : null;
	const words  = notes.split(" ");

	let msg =
		!apiKey
			? "Enter API key."
			: !notes
			? "Enter notes first."
			: words.length > 2500
			? "Notes too long."
			: modelVisible && !model
			? "Enter model."
			: "Generating...";

	StatusLabel.textContent = msg;
	if (!notes || !apiKey || words.length > 2500 || (!model && CustomModel.checked)) return;

	try {
		const body = {
			notes,
			apiKey,
			model,
			language: LanguageSelector.value.trim(),
			apiMode: APIModeSelector.value.trim()
		};

		const res1 = await fetch("/note-enhancer/enhance", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(body)
		});
		const data = await res1.json();

		const res2 = await fetch("/store-notes", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ notes: data.notes })
		});
		const payload = await res2.json();

		window.location.href = `/note-enhancer/result?notes=${encodeURIComponent(payload.id)}`;
	} catch {
		StatusLabel.textContent = "Error while generating flashcards.";
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
		window.location.href = `/note-enhancer/result?notes=${encodeURIComponent(data.id)}`;
    } else {
		StatusLabel.textContent = data.err
	}
}

InitFileUploads({
	onRegularFile: SendFile,
	onImportFile: ImportData
})
