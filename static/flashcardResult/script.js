document.addEventListener('DOMContentLoaded', () => {
    const display = document.getElementById("display");
    if (!display) return console.error("No display element");

    try {
        const flashcardsObj = JSON.parse(display.dataset.notes || '{}');
        const flashcards = Object.values(flashcardsObj);
        
        if (flashcards.length === 0) {
            display.innerHTML = '<div class="no-flashcards">No flashcards generated 😔<br><a href="/flashcardGenerator">Generate some now!</a></div>';
            return;
        }
        
        display.innerHTML = flashcards.map((card, i) => `
            <div class="flashcard" tabindex="0" role="button" aria-expanded="false">
                <div class="question">${card.question}</div>
                <div class="answer">${card.answer}</div>
            </div>
        `).join('');

        display.addEventListener('click', (e) => {
            const flashcard = e.target.closest('.flashcard');
            if (flashcard) flipCard(flashcard);
        });

        display.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const flashcard = e.target.closest('.flashcard');
                if (flashcard) flipCard(flashcard);
            }
        });

    } catch (e) {
        console.error('Flashcard parse error:', e);
        display.textContent = 'Error loading flashcards';
    }
});

function flipCard(card) {
    const isFlipped = card.classList.contains('flipped');
    const question = card.querySelector('.question');
    
    card.classList.toggle('flipped');
    card.setAttribute('aria-expanded', !isFlipped);
    
    if (!isFlipped) {
        question.setAttribute('aria-label', 'Hide answer');
    } else {
        question.setAttribute('aria-label', 'Show answer');
    }
}
