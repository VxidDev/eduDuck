import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js"

(async () => {
    await GetFreeLimitUsage();

    const Display = document.querySelector('.Enhanced');
    const md = window.markdownit({ html: false, linkify: true, typographer: true });

    let raw = JSON.parse(Display.dataset.notes || '""');
	if (typeof raw === "string") raw = raw.trim();

    if (!raw) {
        Display.innerHTML = '<p>Failed to load notes!</p>';
        return;
    }

    Display.innerHTML = md.render(raw);
    Display.innerHTML += '<button class="button export" style="margin-bottom: 25px;">📄 Export Enhanced Notes</button>';

    document.querySelector(".export").addEventListener("click", async () => {
        const params = new URLSearchParams(window.location.search);
        const id = params.get("notes");
        if (!id) return;

        window.open(`/note-enhancer/export-notes?notes=${encodeURIComponent(id)}`);
    });
})();

