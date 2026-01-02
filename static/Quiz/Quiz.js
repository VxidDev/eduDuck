document.addEventListener('DOMContentLoaded', () => {
    const quizContainer = document.getElementById('quizContainer');
    const rawJson = quizContainer.dataset.notes || '""';
    
    try {
        const parsedData = JSON.parse(rawJson);
        window.quizData = parsedData;
        
        if (!parsedData || Object.keys(parsedData).length === 0) {
            quizContainer.innerHTML = '<p>Failed to load quiz!</p>';
            return;
        }
        renderQuiz(parsedData);
        quizContainer.removeAttribute('data-notes');
        document.getElementById('submitQuiz').style.display = 'block';
    } catch (e) {
        quizContainer.innerHTML = '<p>Invalid quiz data!</p>';
        console.error('Quiz parse error:', e);
    }
});

function renderQuiz(quizData) {
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
    document.getElementById('quizContainer').innerHTML = html;
}

document.getElementById('submitQuiz').addEventListener('click', async () => {
    await submitQuiz(window.quizData);
});

async function submitQuiz(quizData) {
    const answers = {};
    for (let num in quizData) {
        const selected = document.querySelector(`input[name="q${num}"]:checked`);
        answers[num] = selected ? selected.value : null;
    }
    
    try {
        const response = await fetch('/quiz-generator/quiz/result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quiz: quizData, answers: answers })
        });
        
        if (!response.ok) throw new Error('Submit failed');
        const result = await response.json();
        window.location.href = `/quiz-generator/quiz/result?result=${encodeURIComponent(JSON.stringify(result))}`;
    } catch (error) {
        alert('Error submitting quiz. Please try again.');
        console.error('Submit error:', error);
    }
}
