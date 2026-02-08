interface NextActionSuggestion {
    action_type: string;
    topic: string;
    reason: string;
    estimated_time_minutes: number;
}

export async function initNextAction(): Promise<void> {
    const btn = document.getElementById('next-action-btn') as HTMLButtonElement;
    const modal = document.getElementById('next-modal') as HTMLElement;
    const overlay = document.getElementById('overlay') as HTMLElement;
    const generateBtn = document.getElementById('generate-btn') as HTMLButtonElement;

    if (!btn || !modal || !overlay || !generateBtn) return;

    let currentSuggestion: NextActionSuggestion | null = null;

    function updateModalTheme(): void {
        const isDark = document.body.classList.contains('dark');
        modal.style.background = isDark ? 'rgb(17 24 39)' : 'white';
        modal.style.color = isDark ? 'rgb(243 244 246)' : 'rgb(17 24 39)';
        modal.style.border = `1px solid ${isDark ? 'rgb(55 65 81)' : 'rgb(229 231 235)'}`;
        modal.style.boxShadow = isDark ?
            '0 25px 50px -12px rgb(0 0 0 / 0.7)' :
            '0 20px 25px -5px rgb(0 0 0 / 0.1)';

        generateBtn.style.background = isDark ? 'rgb(16 185 129)' : '#10b981';
        generateBtn.style.color = 'white';
        generateBtn.style.border = 'none';

        const closeBtn = modal.querySelector('button:not(#generate-btn)') as HTMLButtonElement;
        if (closeBtn) {
            closeBtn.style.color = isDark ? 'rgb(243 244 246)' : 'rgb(17 24 39)';
            closeBtn.style.background = isDark ? 'rgb(55 65 81)' : 'transparent';
            closeBtn.style.border = `1px solid ${isDark ? 'rgb(55 65 81)' : 'rgb(209 213 219)'}`;
        }

        const titleEl = document.getElementById('next-title') as HTMLElement;
        const topicEl = document.getElementById('next-topic') as HTMLElement;
        const reasonEl = document.getElementById('next-reason') as HTMLElement;

        if (titleEl) titleEl.style.color = isDark ? 'rgb(243 244 246)' : 'rgb(17 24 39)';
        if (topicEl) topicEl.style.color = isDark ? 'rgb(34 197 94)' : '#10b981';
        if (reasonEl) reasonEl.style.color = isDark ? 'rgb(156 163 175)' : 'rgb(75 85 99)';
    }

    const themeObserver = new MutationObserver((): void => {
        if (modal.style.display === 'block') {
            updateModalTheme();
        }
    });
    themeObserver.observe(document.body, { attributes: true, attributeFilter: ['class'] });

    btn.addEventListener('click', async (): Promise<void> => {
        try {
            const res = await fetch('/api/next-action');
            if (!res.ok) throw new Error('Failed to fetch suggestion');

            currentSuggestion = await res.json() as NextActionSuggestion;

            const titleEl = document.getElementById('next-title') as HTMLElement;
            const topicEl = document.getElementById('next-topic') as HTMLElement;
            const reasonEl = document.getElementById('next-reason') as HTMLElement;

            if (titleEl) {
                titleEl.textContent =
                    `${currentSuggestion.action_type.charAt(0).toUpperCase() + currentSuggestion.action_type.slice(1)} Time! 🦆`;
            }
            if (topicEl) topicEl.textContent = currentSuggestion.topic;
            if (reasonEl) {
                reasonEl.textContent =
                    `${currentSuggestion.reason} (~${currentSuggestion.estimated_time_minutes} min)`;
            }

            modal.style.display = 'block';
            overlay.style.display = 'block';
            overlay.style.background = document.body.classList.contains('dark') ? 'rgba(0,0,0,0.7)' : 'rgba(0,0,0,0.5)';
            updateModalTheme();
        } catch (err) {
            console.error('Error fetching next action:', err);
            alert('Could not load suggestion. Try again!');
        }
    });

    function closeModal(): void {
        modal.style.display = 'none';
        overlay.style.display = 'none';
    }

    overlay.addEventListener('click', closeModal);
    const closeBtn = modal.querySelector('button:not(#generate-btn)') as HTMLButtonElement;
    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    generateBtn.addEventListener('click', (): void => {
        if (!currentSuggestion) return;
        const baseUrls: Record<string, string> = {
            'quiz': '/quiz-generator',
            'flashcards': '/flashcard-generator',
            'notes': '/note-enhancer'
        };
        const url = `${baseUrls[currentSuggestion.action_type] || '/quiz-generator'}?topic=${encodeURIComponent(currentSuggestion.topic)}`;
        window.location.href = url;
    });
}
