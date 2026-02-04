import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

interface MarkdownitInstance {
    render: (src: string) => string;
}

declare global {
    interface Window {
        markdownit: (options: {
            html: boolean;
            linkify: boolean;
            typographer: boolean;
        }) => MarkdownitInstance;
    }
}

(async () => {
    await GetFreeLimitUsage();

    const display = document.querySelector('.Enhanced') as HTMLElement;
    if (!display) return;

    const md = (window as any).markdownit({ 
        html: false, 
        linkify: true, 
        typographer: true 
    }) as MarkdownitInstance;

    let raw = JSON.parse(display.dataset.notes || '""');
    if (typeof raw === "string") {
        raw = raw.trim();
    }

    if (!raw) {
        display.innerHTML = '<p>Failed to load notes!</p>';
        return;
    }

    display.innerHTML = md.render(raw as string);
    display.innerHTML += '<button class="button export" style="margin-bottom: 25px;">📄 Export Enhanced Notes</button>';

    const exportBtn = document.querySelector(".export") as HTMLButtonElement;
    if (exportBtn) {
        exportBtn.addEventListener("click", handleExport);
    }
})();

function handleExport(): void {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (!id) return;

    window.open(`/note-enhancer/export-notes?notes=${encodeURIComponent(id)}`);
}
