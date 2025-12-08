const Display = document.querySelector('.Enhanced');
const md = window.markdownit({
    html: false,
    linkify: true,
    typographer: true
});

document.addEventListener('DOMContentLoaded', () => {
    const rawJson = Display.dataset.notes || '""';
    const raw = JSON.parse(rawJson);
    const normalized = raw.trim().replace(/\\n/g, '\n');

    if (!normalized) {
        Display.innerHTML = '<p>Failed to load notes!</p>';
        return;
    }

    Display.innerHTML = md.render(normalized);
});
