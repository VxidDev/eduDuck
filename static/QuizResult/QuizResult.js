import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js"

( async () => { await GetFreeLimitUsage(); })();

const params = new URLSearchParams(window.location.search);
const resultJson = params.get("result");

if (resultJson) {
	try {
		const result = JSON.parse(decodeURIComponent(resultJson));
		renderResults(result);
	} catch {
		document.getElementById("resultsList").innerHTML = "<p>Error loading results</p>";
	}
}

function renderResults(result) {
	const scoreDisplay  = document.getElementById("scoreDisplay");
	const percentageEl  = document.getElementById("percentage");
	const totalQuestions= document.getElementById("totalQuestions");
	const resultsList   = document.getElementById("resultsList");

	scoreDisplay.textContent   = `${result.score}/${result.total}`;
	percentageEl.textContent   = `${result.percentage}%`;
	totalQuestions.textContent = `${result.total} questions`;

	let html = "";
	for (const num in result.results) {
		const r      = result.results[num];
		const status = r.right ? "correct" : "wrong";
		html += `
			<div class="result-question ${status}">
				<strong>Q${num}:</strong> You chose <span class="${status}">${r.user || "nothing"}</span> 
				${r.right ? "✅ Correct!" : `❌ Correct was ${r.correct}`}
			</div>`;
	}
	resultsList.innerHTML = html;
}
