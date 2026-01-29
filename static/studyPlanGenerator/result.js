import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

function ParseStudyPlan(planText) {
    if (!planText) return [];
    let parsed;
    try {
        parsed = JSON.parse(planText);
    } catch {
        return [];
    }
    return parsed.map(entry => ({
        day: entry.day || "",
        tasks: entry.tasks || ""
    }));
}

function parseTasks(taskString) {
    return taskString
        .split(/\s*,\s*(?=[A-Za-z]+:)/)
        .map(part => {
            const match = part.match(/^([^:]+):\s*(.+?)\s*\(minutes:\s*(\d+)\)/i);
            if (!match) return null;

            return {
                type: match[1].trim(),
                text: match[2].trim(),
                minutes: parseInt(match[3], 10)
            };
        })
        .filter(Boolean);
}

(async () => {
    await GetFreeLimitUsage();

    const Display = document.querySelector('.md-content');
    let raw = Display.dataset.notes || "";

    try {
        raw = JSON.parse(raw);
        if (typeof raw === "string") raw = raw.trim();
    } catch {
        raw = raw.trim();
    }

    if (!raw) {
        Display.innerHTML = '<p>Failed to load study plan!</p>';
        return;
    }

    const studyPlan = ParseStudyPlan(typeof raw === "string" ? raw : JSON.stringify(raw));
    Display.innerHTML = "";

    studyPlan.forEach(entry => {
        const dayDiv = document.createElement("div");
        dayDiv.className = "study-day";

        const title = document.createElement("h3");
        title.textContent = entry.day;
        dayDiv.appendChild(title);

        const tasks = parseTasks(entry.tasks);

        const ul = document.createElement("ul");
        ul.className = "study-tasks";

        tasks.forEach(task => {
            const li = document.createElement("li");
            li.innerHTML = `
                <strong>${task.type}</strong>: ${task.text}
                <span class="minutes">(${task.minutes} min)</span>
            `;
            ul.appendChild(li);
        });

        dayDiv.appendChild(ul);
        Display.appendChild(dayDiv);
    });

    Display.innerHTML += '<button class="button export" style="margin-bottom: 25px;">📄 Export Study Plan</button>';

    document.querySelector(".export").addEventListener("click", () => {
        const params = new URLSearchParams(window.location.search);
        const id = params.get("plan");
        if (!id) return;
        window.open(`/study-plan-generator/export-plan?plan=${encodeURIComponent(id)}`);
    });
})();
