const NoteInput = document.querySelector(".notes");
const Submit = document.querySelector(".submit");
const OutputDisplay = document.querySelector(".output");
const TextInputs = document.querySelectorAll(".textInput")
const ApiKeyInput = document.querySelector(".apiKey");

TextInputs.forEach(textinput => {
    textinput.addEventListener('input', function() {
        this.style.height = 'auto';           
        this.style.height = this.scrollHeight + 'px';
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
        OutputDisplay.style.height = 'auto';           
        OutputDisplay.style.height = OutputDisplay.scrollHeight + 'px';
    } catch (error) {
        OutputDisplay.textContent = "Error while generating.";
    }
})