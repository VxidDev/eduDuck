import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";
(async () => {
    await GetFreeLimitUsage();
    const display = document.querySelector('.Enhanced');
    if (!display)
        return;
    const md = markdownit({
        html: false,
        linkify: true,
        typographer: true
    });
    let raw;
    try {
        raw = JSON.parse(display.dataset.notes || '""').trim();
    }
    catch (e) {
        display.innerHTML = '<p>Failed to parse notes!</p>';
        return;
    }
    if (!raw) {
        display.innerHTML = '<p>Failed to load notes!</p>';
        return;
    }
    display.innerHTML = md.render(raw);
    const exportButton = document.createElement('button');
    exportButton.classList.add('button', 'export');
    exportButton.style.marginBottom = '25px';
    exportButton.textContent = '📄 Export Enhanced Notes';
    exportButton.addEventListener("click", () => {
        const params = new URLSearchParams(window.location.search);
        const id = params.get("id");
        if (!id)
            return;
        window.open(`/note-enhancer/export-notes?notes=${encodeURIComponent(id)}`);
    });
    display.appendChild(exportButton);
})();
//# sourceMappingURL=EnhancedScript.js.map