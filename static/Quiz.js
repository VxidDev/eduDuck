document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const quizJson = urlParams.get('quiz');
    
    if (quizJson) {
        try {
            const quizData = JSON.parse(decodeURIComponent(quizJson));
            renderQuiz(quizData);
            document.getElementById('submitQuiz').style.display = 'block';
        } catch (e) {
            document.getElementById('quizContainer').innerHTML = '<p>Error loading quiz</p>';
        }
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

document.getElementById('submitQuiz').addEventListener('click', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const quizJson = urlParams.get('quiz');
    const quizData = JSON.parse(decodeURIComponent(quizJson));
    submitQuiz(quizData);
});

async function submitQuiz(quizData) {
    const answers = {};
    for (let num in quizData) {
        const selected = document.querySelector(`input[name="q${num}"]:checked`);
        answers[num] = selected ? selected.value : null;
    }
    
    const response = await fetch('/result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quiz: quizData, answers: answers })
    });
    
    const result = await response.json();
    window.location.href = `/result?result=${encodeURIComponent(JSON.stringify(result))}`;
}
