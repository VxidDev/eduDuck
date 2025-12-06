const NoteInput = document.querySelector(".notes");
const Submit = document.querySelector(".submit");
const OutputDisplay = document.querySelector(".output");
const TextInputs = document.querySelectorAll(".textInput")
const ApiKeyInput = document.querySelector(".apiKey");

TextInputs.forEach(textinput => {
    const MAXLINES = textinput.classList.contains("slim") ?
    1 : textinput.classList.contains("standard") ?
    5 : textinput.classList.contains("large") ?
    20 : 1;
    const LINEHEIGHT = 20;

    textinput.addEventListener('input', function() {        
        this.style.height = Math.min(this.scrollHeight , (MAXLINES * LINEHEIGHT) + 60) + 'px';
    });
});

Submit.addEventListener('click' , async () => {
    const notes = NoteInput.value.trim();
    const apiKey = ApiKeyInput.value.trim();
    
    const msg = !apiKey ? "Enter API key." : 
            !notes ? "Enter notes first." : 
            notes.split(' ').length > 1000 ? "Notes too long." : 
            "Generating...";
    OutputDisplay.textContent = msg; 
    if (!notes || !apiKey || notes.split(' ').length > 1000) return;

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes: notes , apiKey: apiKey})
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