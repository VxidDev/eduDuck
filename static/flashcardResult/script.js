document.addEventListener("DOMContentLoaded", () => {
	const display = document.getElementById("display");
	if (!display) return console.error("No display element");

	try {
		const flashcards = Object.values(JSON.parse(display.dataset.notes || "{}"));

		if (!flashcards.length) {
			display.innerHTML =
				'<div class="no-flashcards">No flashcards generated 😔<br><a href="/flashcardGenerator">Generate some now!</a></div>';
			return;
		}

		display.innerHTML = flashcards
			.map(
				card => `
			<div class="flashcard" tabindex="0" role="button" aria-expanded="false">
				<div class="question">${card.question}</div>
				<div class="answer">${card.answer}</div>
			</div>`
			)
			.join("");

		const handleFlip = e => {
			const card = e.target.closest(".flashcard");
			if (!card) return;
			if (e.type === "click" || e.key === "Enter" || e.key === " ") {
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

function flipCard(card) {
	const isFlipped = card.classList.contains("flipped");
	const question = card.querySelector(".question");

	card.classList.toggle("flipped");
	card.setAttribute("aria-expanded", !isFlipped);
	question.setAttribute("aria-label", isFlipped ? "Show answer" : "Hide answer");
}
