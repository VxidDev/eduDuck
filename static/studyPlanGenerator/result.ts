import { GetFreeLimitUsage } from "../Components/GetFreeLimitUsage.js";

interface StudyPlanEntry {
    day: string;
    tasks: string;
}

interface ParsedTask {
    type: string;
    text: string;
    minutes: number;
}

function ParseStudyPlan(planText: string | null): StudyPlanEntry[] {
    if (!planText) return [];
    let parsed: any;
    try {
        parsed = JSON.parse(planText);
    } catch {
        return [];
    }
    return (parsed || []).map((entry: any): StudyPlanEntry => ({
        day: entry.day || "",
        tasks: entry.tasks || ""
    }));
}

function parseTasks(taskString: string): ParsedTask[] {
    return taskString
        .split(/\s*,\s*(?=[A-Za-z]+:)/)
        .map((part: string): ParsedTask | null => {
            const match: RegExpMatchArray | null = part.match(/^([^:]+):\s*(.+?)\s*\(minutes:\s*(\d+)\)/i);
            if (!match) return null;

            return {
                type: match[1].trim(),
                text: match[2].trim(),
                minutes: parseInt(match[3], 10)
            };
        })
        .filter((task: ParsedTask | null): task is ParsedTask => task !== null);
}

(async () => {
    await GetFreeLimitUsage();

    const display = document.querySelector('.md-content') as HTMLElement;
    if (!display) return;

    let raw: string | any = display.dataset.notes || "";

    try {
        raw = JSON.parse(raw);
        if (typeof raw === "string") raw = raw.trim();
    } catch {
        if (typeof raw === "string") raw = raw.trim();
    }

    if (!raw) {
        display.innerHTML = '<p>Failed to load study plan!</p>';
        return;
    }

    const studyPlan: StudyPlanEntry[] = ParseStudyPlan(typeof raw === "string" ? raw : JSON.stringify(raw));
    display.innerHTML = "";

    studyPlan.forEach((entry: StudyPlanEntry) => {
        const dayDiv: HTMLDivElement = document.createElement("div");
        dayDiv.className = "study-day";

        const title: HTMLHeadingElement = document.createElement("h3");
        title.textContent = entry.day;
        dayDiv.appendChild(title);

        const tasks: ParsedTask[] = parseTasks(entry.tasks);

        const ul: HTMLUListElement = document.createElement("ul");
        ul.className = "study-tasks";

        tasks.forEach((task: ParsedTask) => {
            const li: HTMLLIElement = document.createElement("li");
            li.innerHTML = `
                <strong>${task.type}</strong>: ${task.text}
                <span class="minutes">(${task.minutes} min)</span>
            `;
            ul.appendChild(li);
        });

        dayDiv.appendChild(ul);
        display.appendChild(dayDiv);
    });

    display.innerHTML += '<button class="button export" style="margin-bottom: 25px;">📄 Export Study Plan</button>';

    const exportBtn = document.querySelector(".export") as HTMLButtonElement;
    if (exportBtn) {
        exportBtn.addEventListener("click", (): void => {
            const params = new URLSearchParams(window.location.search);
            const id = params.get("plan");
            if (!id) return;
            window.open(`/study-plan-generator/export-plan?plan=${encodeURIComponent(id)}`);
        });
    }
})();