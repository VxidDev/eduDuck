const urlParams = new URLSearchParams(window.location.search);
const resultJson = urlParams.get('result');

if (resultJson) {
    try {
        const result = JSON.parse(decodeURIComponent(resultJson));
        renderResults(result);
    } catch (e) {
        document.getElementById('resultsList').innerHTML = '<p>Error loading results</p>';
    }
}

function renderResults(result) {
    document.getElementById('scoreDisplay').textContent = `${result.score}/${result.total}`;
    document.getElementById('percentage').textContent = `${result.percentage}%`;
    document.getElementById('totalQuestions').textContent = `${result.total} questions`;
    
    let html = '';
    for (let num in result.results) {
        const r = result.results[num];
        const status = r.right ? 'correct' : 'wrong';
        html += `
            <div class="result-question ${status}">
                <strong>Q${num}:</strong> You chose <span class="${status}">${r.user || 'nothing'}</span> 
                ${r.right ? '✅ Correct!' : `❌ Correct was ${r.correct}`}
            </div>
        `;
    }
    document.getElementById('resultsList').innerHTML = html;
}