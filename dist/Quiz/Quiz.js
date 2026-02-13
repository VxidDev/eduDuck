import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";
(async () => {
    document.addEventListener('DOMContentLoaded', async () => {
        await GetFreeLimitUsage();
        const quizContainer = document.getElementById('quizContainer');
        const submitQuizBtn = document.getElementById('submitQuiz');
        const exportBtn = document.querySelector(".export");
        const rawJson = quizContainer.dataset.notes || '""';
        try {
            const parsedData = JSON.parse(rawJson);
            if (!parsedData || Object.keys(parsedData).length === 0) {
                quizContainer.innerHTML = `
                    <div class="quiz-error">
                        <h3>⚠️ Failed to load quiz!</h3>
                        <p>Please try again or contact support.</p>
                    </div>
                `;
                return;
            }
            const renderQuiz = (quizData) => {
                let html = '';
                for (const num in quizData) {
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
                quizContainer.innerHTML = html;
            };
            const submitQuiz = async (quizData) => {
                const answers = {};
                for (const num in quizData) {
                    const selected = document.querySelector(`input[name="q${num}"]:checked`);
                    answers[num] = selected ? selected.value : null;
                }
                try {
                    const response = await fetch('/quiz-generator/quiz/result', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ quiz: quizData, answers })
                    });
                    if (!response.ok)
                        throw new Error('Submit failed');
                    const result = await response.json();
                    window.location.href = `/quiz-generator/quiz/result?result=${encodeURIComponent(result.id)}`;
                }
                catch (error) {
                    alert('Error submitting quiz. Please try again.');
                    console.error('Submit error:', error);
                }
            };
            const handleExport = () => {
                const params = new URLSearchParams(window.location.search);
                const id = params.get("id");
                if (!id)
                    return;
                window.open(`/quiz-generator/export-quiz?quiz=${encodeURIComponent(id)}`);
            };
            renderQuiz(parsedData);
            quizContainer.removeAttribute('data-notes');
            submitQuizBtn.style.display = 'flex';
            submitQuizBtn.addEventListener('click', () => submitQuiz(parsedData));
            if (exportBtn) {
                exportBtn.addEventListener("click", handleExport);
            }
        }
        catch (e) {
            quizContainer.innerHTML = `
                <div class="quiz-error" style="padding: 2rem; text-align: center; color: var(--text-heading);">
                    <h3 style="color: var(--accent-danger); margin-bottom: 1rem;">⚠️ Invalid quiz data!</h3>
                    <p style="color: var(--text-muted);">The quiz format is corrupted.</p>
                </div>
            `;
            console.error('Quiz parse error:', e);
        }
    });
})();
//# sourceMappingURL=Quiz.js.map