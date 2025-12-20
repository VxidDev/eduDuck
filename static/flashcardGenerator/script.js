const NoteInput = document.querySelector(".notes");
const Submit = document.querySelector(".submit");
const StatusLabel = document.querySelector(".status");
const TextInputs = document.querySelectorAll(".textInput");
const ApiKeyInput = document.querySelector(".apiKey");
const FileInputs = document.querySelectorAll(".file-upload-wrapper");
const CustomModel = document.getElementById("customModel");
const CustomModelLabel = document.getElementById("customModelLabel");
const CustomModelInput = document.querySelector(".customModelInput");
const LanguageSelector = document.getElementById('language');
const APIModeSelector = document.getElementById("apiMode");
const AmountSelector = document.getElementById("questionCount");

let IsHuggingFace = true;

CustomModel.addEventListener('change', () => {
    if (CustomModel.checked) {
        CustomModelInput.classList.remove("hidden");
    } else {
        CustomModelInput.classList.add("hidden");
    }
});

APIModeSelector.addEventListener('change' , () => {
    ApiKeyInput.placeholder = `Enter your ${APIModeSelector.value} API key here!`;
    IsHuggingFace = APIModeSelector.value == "Hugging Face" ? true : false;
    if (!IsHuggingFace) {
        if (CustomModel.checked) {
            CustomModel.checked = false;
            CustomModelInput.classList.add("hidden");
        }
        CustomModel.classList.add("hidden");
        CustomModelLabel.classList.add("hidden");
    } else {
        CustomModel.classList.remove("hidden");
        CustomModelLabel.classList.remove("hidden");
    };
})

TextInputs.forEach(textinput => {
    const MAXLINES = textinput.classList.contains("slim")
        ? 1
        : textinput.classList.contains("standard")
        ? 5
        : textinput.classList.contains("large")
        ? 20
        : 1;
    const LINEHEIGHT = 25;

    textinput.addEventListener('input', function () {
        this.style.height = 'auto';
        const newHeight = Math.min(
            this.scrollHeight,
            (MAXLINES * LINEHEIGHT) + 35
        );
        this.style.height = newHeight + 'px';
    });
});

Submit.addEventListener('click', async () => {
    const notes = NoteInput.value.trim();
    const apiKey = ApiKeyInput.value.trim();
    let model = null;

    let msg = !apiKey ? "Enter API key."
        : !notes ? "Enter notes first."
        : notes.split(' ').length > 2500 ? "Notes too long."
        : "Generating...";

    if (!CustomModelInput.classList.contains("hidden")) {
        model = CustomModelInput.value.trim();
        if (!model) {
            msg = "Enter model.";
        }
    } else {
        model = null;
    }

    StatusLabel.textContent = msg;
    if (!notes || !apiKey || notes.split(' ').length > 2500 || (!model && CustomModel.checked)) return;

    try {
        const body = {
            notes: notes,
            apiKey: apiKey,
            model: model,
            language: LanguageSelector.value.trim(),
            apiMode: APIModeSelector.value.trim(),
            amount: AmountSelector.value.trim()
        };

        const response = await fetch('/flashcard-generator/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        const res = await fetch('/store-flashcards', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ flashcards: data.flashcards })
        });

        const payload = await res.json();

        window.location.href = `/flashcard-generator/result?id=${encodeURIComponent(payload.id)}`;
    } catch (error) {
        StatusLabel.textContent = "Error while generating flashcards.";
    }
});

async function SendFile(file) {
    const formData = new FormData();
    formData.append("notesFile", file);

    NoteInput.textContent = "Loading...";

    const response = await fetch('/upload-notes', {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        NoteInput.textContent = "File upload failed.";
        return;
    }

    const data = await response.json();
    NoteInput.textContent = data.notes;

    const MAXLINES = NoteInput.classList.contains("slim")
        ? 1
        : NoteInput.classList.contains("standard")
        ? 5
        : NoteInput.classList.contains("large")
        ? 20
        : 1;
    const LINEHEIGHT = 20;
    NoteInput.style.height = Math.min(
        NoteInput.scrollHeight,
        (MAXLINES * LINEHEIGHT) + 60
    ) + 'px';
}

window.addEventListener('load', function () {
    const fileInputs = document.querySelectorAll('.file-input');

    fileInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            const wrapper = this.closest('.file-upload-wrapper');
            const displayElement = wrapper.querySelector('.fileButton');

            if (this.files.length > 0) {
                const fileNames = Array.from(this.files).map(f => f.name).join(', ');
                displayElement.textContent = fileNames.length > 30
                    ? `${fileNames.substring(0, 27)}...`
                    : fileNames;
                displayElement.classList.add('has-file');
                SendFile(this.files[0]);
            } else {
                displayElement.textContent = 'No file selected';
                displayElement.classList.remove('has-file');
            }
        });
    });
});
