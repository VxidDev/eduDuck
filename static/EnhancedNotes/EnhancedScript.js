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
	Display.innerHTML += '<button class="button export" style="margin-bottom: 25px;">📄 Export Quiz</button>';

	document.querySelector(".export").addEventListener("click", async () => {
		const params = new URLSearchParams(window.location.search);
		const id = params.get("notes");
		if (!id) return;

		window.open(`/note-enhancer/export-notes?notes=${encodeURIComponent(id)}`)
	});
});
