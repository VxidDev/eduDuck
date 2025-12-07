const NoteInput = document.querySelector(".notes");
const Submit = document.querySelector(".submit");
const OutputDisplay = document.querySelector(".output");
const TextInputs = document.querySelectorAll(".textInput")
const ApiKeyInput = document.querySelector(".apiKey");
const FileInputs = document.querySelectorAll(".file-upload-wrapper");
const CustomModel = document.getElementById("customModel");
const CustomModelInput = document.querySelector(".customModelInput");

CustomModel.addEventListener('change' , () => {
    if (CustomModel.checked) {
        CustomModelInput.classList.remove("hidden");
    } else {
        CustomModelInput.classList.add("hidden");
    }
})

TextInputs.forEach(textinput => {
    const MAXLINES = textinput.classList.contains("slim") ?
    1 : textinput.classList.contains("standard") ?
    5 : textinput.classList.contains("large") ?
    20 : 1;
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

Submit.addEventListener('click' , async () => {
    const notes = NoteInput.value.trim();
    const apiKey = ApiKeyInput.value.trim();
    let model = null;
    
    let msg = !apiKey ? "Enter API key." : 
            !notes ? "Enter notes first." : 
            notes.split(' ').length > 2500 ? "Notes too long." : 
            "Generating...";

    if (!CustomModelInput.classList.contains("hidden")) {
        model = CustomModelInput.value.trim();
        if (!model) {
            msg = "Enter model.";
        } 
    } else {
        model = false;
    }

    OutputDisplay.textContent = msg; 
    if (!notes || !apiKey || notes.split(' ').length > 2500 || (!model && model !== false)) return;

    try {
        let body = {notes: notes, apiKey: apiKey}
        if (model) body["model"] = model
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        OutputDisplay.innerHTML = data.quiz;
        const MAXLINES = OutputDisplay.classList.contains("slim") ?
        1 : OutputDisplay.classList.contains("standard") ?
        5 : OutputDisplay.classList.contains("large") ?
        20 : 1;
        const LINEHEIGHT = 20;           
        OutputDisplay.style.height = Math.min(OutputDisplay.scrollHeight , (MAXLINES * LINEHEIGHT) + 60) + 'px';
    } catch (error) {
        OutputDisplay.textContent = "Error while generating.";
    }
})

async function SendFile(file) {
    const formData = new FormData();

    formData.append("notesFile" , file);

    NoteInput.textContent = "Loading..."

    const response = await fetch('/upload-notes' , {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        NoteInput.textContent = "File upload failed.";
        return;
    }

    const data = await response.json();
    NoteInput.textContent = data.notes;
     const MAXLINES = NoteInput.classList.contains("slim") ?
        1 : NoteInput.classList.contains("standard") ?
        5 : NoteInput.classList.contains("large") ?
        20 : 1;
        const LINEHEIGHT = 20;           
        NoteInput.style.height = Math.min(NoteInput.scrollHeight , (MAXLINES * LINEHEIGHT) + 60) + 'px';
}

window.addEventListener('load', function() {
    const fileInputs = document.querySelectorAll('.file-input');
  
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const wrapper = this.closest('.file-upload-wrapper');
            displayElement = wrapper.querySelector('.fileButton');
        
            if (this.files.length > 0) {
                const fileNames = Array.from(this.files).map(f => f.name).join(', ');
                displayElement.textContent = fileNames.length > 30 ? 
                `${fileNames.substring(0, 27)}...` : fileNames;
                displayElement.classList.add('has-file');
                SendFile(this.files[0])
            } else {
                displayElement.textContent = 'No file selected';
                displayElement.classList.remove('has-file');
            }
        });
    });
});