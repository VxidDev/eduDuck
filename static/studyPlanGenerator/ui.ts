export const NoteInput = document.querySelector<HTMLTextAreaElement>(".notes")!;
export const Submit = document.querySelector<HTMLButtonElement>(".submit")!;
export const TextInputs = document.querySelectorAll<HTMLTextAreaElement>(".textInput");
export const ApiKeyInput = document.querySelector<HTMLInputElement>(".apiKey")!;
export const ApiKeyInputParent = ApiKeyInput ? ApiKeyInput.closest('.textInput-wrapper') as HTMLElement : null;
export const CustomModel = document.getElementById("customModel") as HTMLInputElement;
export const CustomModelInput = document.querySelector<HTMLInputElement>(".customModelInput")!;
export const LanguageSelector = document.getElementById("output-language") as HTMLSelectElement;
export const APIModeSelector = document.getElementById("apiMode") as HTMLSelectElement;
export const FreeUsage = document.getElementById("FreeUsage") as HTMLInputElement | null;
export const FreeUsageText = document.getElementById("FreeUsageText") as HTMLElement | null;

export const StartDateInput = document.getElementById("startDate") as HTMLInputElement;
export const EndDateInput = document.getElementById("endDate") as HTMLInputElement;
export const HoursInput = document.getElementById("hoursPerDay") as HTMLInputElement;
export const LearningStyleInputs = document.querySelectorAll<HTMLInputElement>(".learningStyle");
export const GoalInput = document.getElementById("studyGoal") as HTMLInputElement;
