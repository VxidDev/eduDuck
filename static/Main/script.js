const NoteInput = document.querySelector(".notes");
const Submit = document.querySelector(".submit");
const StatusLabel = document.querySelector(".status");
const TextInputs = document.querySelectorAll(".textInput");
const ApiKeyInput = document.querySelector(".apiKey");
const FileInputs = document.querySelectorAll(".file-upload-wrapper");
const CustomModel = document.getElementById("customModel");
const CustomModelInput = document.querySelector(".customModelInput");
const ModeSelector = document.querySelector('select[name="Content"]');
const StudyPlan = document.querySelector('.studyPlan');

CustomModel.addEventListener('change', () => {
    if (CustomModel.checked) {
        CustomModelInput.classList.remove("hidden");
    } else {
        CustomModelInput.classList.add("hidden");
    }
});

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

function cleanHtmlForTextarea(html) {
    return html
        .replace(/ /g, ' ')
        .replace(/\u00A0/g, ' ')
        .replace(/[\u2011\u2012\u2013\u2014\u2015‑]/g, '-')
        .replace(/<[^>]*>/g, '')
        .replace(/\n\s*\n\s*\n/g, '\n\n')
        .trim();
}

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
            mode: ModeSelector.value,
            model: model
        };

        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (ModeSelector.value === "enhanceNotes") {
            const res = await fetch('/store-notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: data.notes })
            });

            const payload = await res.json();
            window.location.href = `/enhancedNotes?id=${encodeURIComponent(payload.id)}`;
            return;
        } else if (ModeSelector.value === "quiz") {
            window.location.href = `/quiz?quiz=${encodeURIComponent(JSON.stringify(data))}`;
        } else if (ModeSelector.value === "flashCards") {
            window.location.href = `/flashcards`;
        } else if (ModeSelector.value === "studyPlan") {
            StudyPlan.classList.remove("hidden");
            StudyPlan.textContent = data.studyPlan;
        }
    } catch (error) {
        StatusLabel.textContent = "Error while generating quiz.";
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
