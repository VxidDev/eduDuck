import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

// Define interfaces for type safety
interface QuizQuestion {
    question: string;
    answers: {
        a: string;
        b: string;
        c: string;
        d: string;
    };
}

interface QuizData {
    [key: string]: QuizQuestion;
}

interface SubmitData {
    quiz: QuizData;
    answers: { [key: string]: string | null };
}

// IIFE for GetFreeLimitUsage
(async () => {
    await GetFreeLimitUsage();
})();

document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quizContainer') as HTMLElement;
    const submitQuizBtn = document.getElementById('submitQuiz') as HTMLButtonElement;
    const exportBtn = document.querySelector(".export") as HTMLButtonElement;
    
    const rawJson = quizContainer.dataset.notes || '""';
    
    try {
        const parsedData: QuizData = JSON.parse(rawJson);
        window.quizData = parsedData;
        
        if (!parsedData || Object.keys(parsedData).length === 0) {
            quizContainer.innerHTML = `
                <div class="quiz-error">
                    <h3>⚠️ Failed to load quiz!</h3>
                    <p>Please try again or contact support.</p>
                </div>
            `;
            return;
        }

        renderQuiz(parsedData);
        quizContainer.removeAttribute('data-notes');
        submitQuizBtn.style.display = 'flex';

        // Add submit event listener
        submitQuizBtn.addEventListener('click', async () => {
            await submitQuiz(parsedData);
        });

        // Add export event listener
        if (exportBtn) {
            exportBtn.addEventListener("click", handleExport);
        }
    } catch (e) {
        quizContainer.innerHTML = `
            <div class="quiz-error" style="padding: 2rem; text-align: center; color: var(--text-heading);">
                <h3 style="color: var(--accent-danger); margin-bottom: 1rem;">⚠️ Invalid quiz data!</h3>
                <p style="color: var(--text-muted);">The quiz format is corrupted.</p>
            </div>
        `;
        console.error('Quiz parse error:', e);
    }
});

declare global {
    interface Window {
        quizData: QuizData;
    }
}

function renderQuiz(quizData: QuizData): void {
    let html = '';
    for (let num in quizData) {
        const q = quizData[num];
        html += `
            <div class="quiz-question" data-num="${num}">
                <h3>${num}. ${q.question}</h3>
                <label class="quiz-option" data-answer="a"><input type="radio" name="q${num}" value="a"> a) ${q.answers.a}</label>
                <label class="quiz-option" data-answer="b"><input type="radio" name="q${num}" value="b"> b) ${q.answers.b}</label>
                <label class="quiz-option" data-answer="c"><input type="radio" name="q${num}" value="c"> c) ${q.answers.c}</label>
                <label class="quiz-option" data-answer="d"><input type="radio" name="q${num}" value="d"> d) ${q.answers.d}</label>
            </div>
        `;
    }
    const quizContainer = document.getElementById('quizContainer') as HTMLElement;
    quizContainer.innerHTML = html;
}

async function submitQuiz(quizData: QuizData): Promise<void> {
    const answers: { [key: string]: string | null } = {};
    for (let num in quizData) {
        const selected = document.querySelector(`input[name="q${num}"]:checked`) as HTMLInputElement | null;
        answers[num] = selected ? selected.value : null;
    }
    
    try {
        const response = await fetch('/quiz-generator/quiz/result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quiz: quizData, answers })
        });
        
        if (!response.ok) throw new Error('Submit failed');

        const result = await response.json() as { id: string };
        window.location.href = `/quiz-generator/quiz/result?result=${encodeURIComponent(result.id)}`;
    } catch (error) {
        alert('Error submitting quiz. Please try again.');
        console.error('Submit error:', error);
    }
}

function handleExport(): void {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("id");
    if (!id) return;

    window.open(`/quiz-generator/export-quiz?quiz=${encodeURIComponent(id)}`);
}
