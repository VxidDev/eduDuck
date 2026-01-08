import { ValidateInput } from "../Components/ValidateInput.js";
import { CustomModelListeners } from "../Components/ModelSelector.js"
import { InitFileUploads } from "../Components/FileUploadHandler.js";

const NoteInput          = document.querySelector(".notes");
const Submit             = document.querySelector(".submit");
const StatusLabel        = document.querySelector(".status");
const TextInputs         = document.querySelectorAll(".textInput");
const ApiKeyInput        = document.querySelector(".apiKey");
const CustomModel        = document.getElementById("customModel");
const CustomModelInput   = document.querySelector(".customModelInput");
const LanguageSelector   = document.getElementById("language");
const APIModeSelector    = document.getElementById("apiMode");
const AmountSelector     = document.getElementById("questionCount");
const CustomModelSelector= document.querySelector(".customModelSelector");

StatusLabel.textContent = '';

CustomModelListeners();

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
	StatusLabel.textContent = "";

	const notes   = NoteInput.value.trim();
	const apiKey  = ApiKeyInput.value.trim();
	const modelVisible = !CustomModelInput.classList.contains("hidden");
	const model   = modelVisible ? CustomModelInput.value.trim() : null;

	ValidateInput(
		notes,
		apiKey,
		modelVisible,
		model,
		StatusLabel,
		notes.split(" ")
	);

	if (!notes || !apiKey || notes.split(" ").length > 2500 || (!model && CustomModel.checked)) return;

	try {
		const body = {
			notes,
			apiKey,
			model,
			language: LanguageSelector.value.trim(),
			apiMode: APIModeSelector.value.trim(),
			amount: AmountSelector.value.trim()
		};

		const res1 = await fetch("/flashcard-generator/generate", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify(body)
		});
		const data = await res1.json();

		const res2 = await fetch("/store-flashcards", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ flashcards: data.flashcards })
		});
		const payload = await res2.json();

		window.location.href = `/flashcard-generator/result?id=${encodeURIComponent(payload.id)}`;
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
