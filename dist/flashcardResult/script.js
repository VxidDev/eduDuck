import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";
(async () => {
    document.addEventListener("DOMContentLoaded", async () => {
        await GetFreeLimitUsage();
        const display = document.getElementById("display");
        if (!display) {
            console.error("No display element");
            return;
        }
        try {
            const flashcardsRaw = JSON.parse(display.dataset.notes || "[]");
            const flashcards = Object.values(flashcardsRaw);
            if (!flashcards.length) {
                display.innerHTML = `
                    <div class="no-flashcards">
                        No flashcards generated<br>
                        <a href="/flashcard-generator">Generate some now!</a>
                    </div>`;
                return;
            }
            display.innerHTML = flashcards
                .map((card) => `
                    <div class="flashcard" tabindex="0" role="button" aria-expanded="false">
                        <div class="question">${card.question}</div>
                        <div class="answer">${card.answer}</div>
                    </div>`)
                .join("");
            const flipCard = (card) => {
                const isFlipped = card.classList.contains("flipped");
                const question = card.querySelector(".question");
                card.classList.toggle("flipped");
                card.setAttribute("aria-expanded", String(!isFlipped));
                question.setAttribute("aria-label", isFlipped ? "Show answer" : "Hide answer");
            };
            const handleFlip = (e) => {
                const card = e.target?.closest(".flashcard");
                if (!card)
                    return;
                if (e.type === "click" || (e instanceof KeyboardEvent && (e.key === "Enter" || e.key === " "))) {
                    e.preventDefault();
                    flipCard(card);
                }
            };
            display.addEventListener("click", handleFlip);
            display.addEventListener("keydown", handleFlip);
        }
        catch (e) {
            console.error("Flashcard parse error:", e);
            display.textContent = "Error loading flashcards";
        }
        const exportBtn = document.querySelector(".export");
        if (exportBtn) {
            exportBtn.addEventListener("click", () => {
                const params = new URLSearchParams(window.location.search);
                const id = params.get("id");
                if (!id)
                    return;
                window.open(`/flashcard-generator/export-flashcards?id=${encodeURIComponent(id)}`);
            });
        }
    });
})();
//# sourceMappingURL=script.js.map