import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

interface Flashcard {
    question: string;
    answer: string;
}

(async () => { 
    await GetFreeLimitUsage(); 
})();

document.addEventListener("DOMContentLoaded", () => {
    const display = document.getElementById("display") as HTMLElement;
    if (!display) {
        console.error("No display element");
        return;
    }

    try {
        const flashcardsRaw = JSON.parse(display.dataset.notes || "[]");
        const flashcards: Flashcard[] = Object.values(flashcardsRaw);

        if (!flashcards.length) {
            display.innerHTML = `
                <div class="no-flashcards">
                    No flashcards generated<br>
                    <a href="/flashcard-generator">Generate some now!</a>
                </div>`;
            return;
        }

        display.innerHTML = flashcards
            .map((card: Flashcard) => `
                <div class="flashcard" tabindex="0" role="button" aria-expanded="false">
                    <div class="question">${card.question}</div>
                    <div class="answer">${card.answer}</div>
                </div>`)
            .join("");

        const handleFlip = (e: MouseEvent | KeyboardEvent): void => {
            const card = (e.target as HTMLElement)?.closest(".flashcard") as HTMLElement;
            if (!card) return;
            
            if (e.type === "click" || (e as KeyboardEvent).key === "Enter" || (e as KeyboardEvent).key === " ") {
                e.preventDefault?.();
                flipCard(card);
            }
        };

        display.addEventListener("click", handleFlip);
        display.addEventListener("keydown", handleFlip);
    } catch (e) {
        console.error("Flashcard parse error:", e);
        display.textContent = "Error loading flashcards";
    }
});

function flipCard(card: HTMLElement): void {
    const isFlipped = card.classList.contains("flipped");
    const question = card.querySelector(".question") as HTMLElement;

    card.classList.toggle("flipped");
    card.setAttribute("aria-expanded", (!isFlipped).toString());
    question.setAttribute("aria-label", isFlipped ? "Show answer" : "Hide answer");
}

const exportBtn = document.querySelector(".export") as HTMLButtonElement;
if (exportBtn) {
    exportBtn.addEventListener("click", (): void => {
        const params = new URLSearchParams(window.location.search);
        const id = params.get("id");
        if (!id) return;

        window.open(`/flashcard-generator/export-flashcards?id=${encodeURIComponent(id)}`);
    });
}