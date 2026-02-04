import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

// Define interfaces for type safety
interface QuizResultItem {
    user: string | null;
    correct: string;
    right: boolean;
}

interface QuizResults {
    score: number;
    total: number;
    percentage: number;
    results: { [key: string]: QuizResultItem };
}

// IIFE for GetFreeLimitUsage
(async () => {
    await GetFreeLimitUsage();
})();

document.addEventListener('DOMContentLoaded', () => {
    const mainContainer = document.querySelector('.main') as HTMLElement;
    let resultsString = mainContainer.dataset.results || '';

    // Convert Python-style strings to valid JSON
    resultsString = resultsString
        .replace(/'/g, '"')
        .replace(/\bTrue\b/g, "true")
        .replace(/\bFalse\b/g, "false")
        .replace(/\bNone\b/g, "null");
    
    try {
        const resultJSON: QuizResults = JSON.parse(resultsString);
        renderResults(resultJSON);
    } catch {
        const resultsList = document.getElementById("resultsList") as HTMLElement;
        resultsList.innerHTML = "<p>Error loading results</p>";
    }
});

function renderResults(result: QuizResults): void {
    const scoreDisplay = document.getElementById("scoreDisplay") as HTMLElement;
    const percentageEl = document.getElementById("percentage") as HTMLElement;
    const totalQuestions = document.getElementById("totalQuestions") as HTMLElement;
    const resultsList = document.getElementById("resultsList") as HTMLElement;

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
}
