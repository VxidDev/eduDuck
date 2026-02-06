export interface NoteAnalysisSection {
    title: string;
    confidence: number;
    issues: string[];
    why_it_matters: string[];
    suggestions: string[];
}

export interface NoteAnalysisResult {
    overall_score: number;
    sections: NoteAnalysisSection[];
}

export interface AnalyzeNotesRequest {
    notes: string;
    language: string;
    apiMode: string;
    apiKey?: string;
    model?: string;
    temperature?: number;
    top_p?: number;
    isFree?: boolean;
}

export interface AnalyzeNotesResponse {
    id?: string;
    analysis?: string;
    error?: string;
}

export async function analyzeNotes(params: AnalyzeNotesRequest): Promise<AnalyzeNotesResponse> {
    try {
        const res = await fetch("/note-analyzer/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                notes: params.notes,
                language: params.language,
                apiMode: params.apiMode,
                apiKey: params.apiKey ?? "",
                model: params.model ?? "",
                temperature: params.temperature ?? 0.3,
                top_p: params.top_p ?? 0.9,
                isFree: params.isFree ?? false,
            }),
        });

        if (!res.ok) {
            return { error: `HTTP ${res.status}` };
        }

        return await res.json() as AnalyzeNotesResponse;
    } catch (e) {
        console.error(e);
        return { error: e instanceof Error ? e.message : "Unknown error" };
    }
}