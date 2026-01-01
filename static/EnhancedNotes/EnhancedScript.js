const Display = document.querySelector('.Enhanced');
const md = window.markdownit({ html: false, linkify: true, typographer: true });

document.addEventListener('DOMContentLoaded', () => {
	const raw = JSON.parse(Display.dataset.notes || '""')
		.trim()
		.replace(/\\n/g, '\n');

	if (!raw) {
		Display.innerHTML = '<p>Failed to load notes!</p>';
		return;
	}

	Display.innerHTML = md.render(raw);
});
