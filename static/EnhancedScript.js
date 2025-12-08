const Display = document.querySelector('.Enhanced');
const md = window.markdownit({
    html: false,
    linkify: true,
    typographer: true
});

function normalizeParsed(text) {
    return text
        .replace(/^"/, '') 
        .replace(/"$/, '')    
        .trim();
}

document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const notesJson = urlParams.get('notes');
    
    if (notesJson) {
        try {
            const decodedNotes = decodeURIComponent(notesJson);
            const notes = decodedNotes.replace(/\\n/g, '\n');
            const normalized = normalizeParsed(notes);
            Display.innerHTML = md.render(normalized);
        } catch (e) {
            Display.innerHTML = '<p>Failed to load notes.</p>';
        }
    }
});
