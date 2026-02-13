import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";
(() => {
    const ParseStudyPlan = (planText) => {
        if (!planText)
            return [];
        let parsed;
        try {
            parsed = JSON.parse(planText);
        }
        catch {
            return [];
        }
        return (parsed || []).map((entry) => ({
            day: entry.day || "",
            tasks: entry.tasks || ""
        }));
    };
    const parseTasks = (taskString) => {
        return taskString
            .split(/\s*,\s*(?=[A-Za-z]+:)/)
            .map((part) => {
            const match = part.match(/^([^:]+):\s*(.+?)\s*\(minutes:\s*(\d+)\)/i);
            if (!match)
                return null;
            return {
                type: match[1].trim(),
                text: match[2].trim(),
                minutes: parseInt(match[3], 10)
            };
        })
            .filter((task) => task !== null);
    };
    (async () => {
        await GetFreeLimitUsage();
        const display = document.querySelector('.md-content');
        if (!display)
            return;
        let raw = display.dataset.notes || "";
        try {
            raw = JSON.parse(raw);
            if (typeof raw === "string")
                raw = raw.trim();
        }
        catch {
            if (typeof raw === "string")
                raw = raw.trim();
        }
        if (!raw) {
            display.innerHTML = '<p>Failed to load study plan!</p>';
            return;
        }
        const studyPlan = ParseStudyPlan(typeof raw === "string" ? raw : JSON.stringify(raw));
        display.innerHTML = "";
        studyPlan.forEach((entry) => {
            const dayDiv = document.createElement("div");
            dayDiv.className = "study-day";
            const title = document.createElement("h3");
            title.textContent = entry.day;
            dayDiv.appendChild(title);
            const tasks = parseTasks(entry.tasks);
            const ul = document.createElement("ul");
            ul.className = "study-tasks";
            tasks.forEach((task) => {
                const li = document.createElement("li");
                li.innerHTML = `
                    <strong>${task.type}</strong>: ${task.text}
                    <span class="minutes">(${task.minutes} min)</span>
                `;
                ul.appendChild(li);
            });
            dayDiv.appendChild(ul);
            display.appendChild(dayDiv);
        });
        const exportButton = document.createElement('button');
        exportButton.classList.add('button', 'export');
        exportButton.style.marginBottom = '25px';
        exportButton.textContent = '📄 Export Study Plan';
        exportButton.addEventListener('click', () => {
            const params = new URLSearchParams(window.location.search);
            const id = params.get("plan");
            if (!id)
                return;
            window.open(`/study-plan-generator/export-plan?plan=${encodeURIComponent(id)}`);
        });
        display.appendChild(exportButton);
    })();
})();
//# sourceMappingURL=result.js.map