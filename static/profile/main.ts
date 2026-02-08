import { loadPFP, initPFPForm } from "./pfp.js";
import { initNextAction } from "./nextAction.js";
import { StudyStreakHeatmap } from "./heatmap.js";

document.addEventListener('DOMContentLoaded', async () => {
    await loadPFP();
    initPFPForm();
    initNextAction();
    new StudyStreakHeatmap('heatmap', 'heatmap-tooltip');
});
