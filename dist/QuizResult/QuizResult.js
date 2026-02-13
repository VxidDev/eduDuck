import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";
(async () => {
    document.addEventListener('DOMContentLoaded', async () => {
        await GetFreeLimitUsage();
        const mainContainer = document.querySelector('.main');
        let resultsString = mainContainer.dataset.results || '';
        resultsString = resultsString
            .replace(/'/g, '"')
            .replace(/\bTrue\b/g, "true")
            .replace(/\bFalse\b/g, "false")
            .replace(/\bNone\b/g, "null");
        try {
            const resultJSON = JSON.parse(resultsString);
            const renderResults = (result) => {
                const scoreDisplay = document.getElementById("scoreDisplay");
                const percentageEl = document.getElementById("percentage");
                const totalQuestions = document.getElementById("totalQuestions");
                const resultsList = document.getElementById("resultsList");
                scoreDisplay.textContent = `${result.score}/${result.total}`;
                percentageEl.textContent = `${result.percentage}%`;
                totalQuestions.textContent = `${result.total} questions`;
                let html = "";
                for (const num in result.results) {
                    const r = result.results[num];
                    const status = r.right ? "correct" : "wrong";
                    html += `
                        <div class="result-question ${status}">
                            <strong>Q${num}:</strong> You chose <span class="${status}">${r.user || "nothing"}</span> 
                            ${r.right ? "✅ Correct!" : `❌ Correct was ${r.correct}`}
                        </div>`;
                }
                resultsList.innerHTML = html;
            };
            renderResults(resultJSON);
        }
        catch {
            const resultsList = document.getElementById("resultsList");
            resultsList.innerHTML = "<p>Error loading results</p>";
        }
    });
})();
//# sourceMappingURL=QuizResult.js.map