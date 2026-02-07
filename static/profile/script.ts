import { GetUserPFP } from "../Components/GetUserPFP.js";

interface StreakDay {
    date: string;
    count: number;
    weekday: number;
}

interface StreakData {
    data: StreakDay[];
    currentStreak: string;
    longestStreak: string;
    totalDays: string;
    totalActivities: string;
}

interface NextActionSuggestion {
    action_type: string;
    topic: string;
    reason: string;
    estimated_time_minutes: number;
}

// Profile Picture Handling
async function loadPFP(): Promise<void> {
    const url: string | null = await GetUserPFP();
    const pfpImg = document.getElementById('user-pfp') as HTMLImageElement;
    if (url && pfpImg) {
        pfpImg.src = url;
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    const form = document.getElementById('profile-pic-form') as HTMLFormElement;
    const status = document.getElementById('profile-pic-status') as HTMLElement;

    if (form) {
        form.addEventListener('submit', async (e: Event): Promise<void> => {
            e.preventDefault();
            const input = document.getElementById('profile-picture-input') as HTMLInputElement;
            
            if (!input?.files?.length) {
                status.textContent = "Please select a file to upload.";
                return;
            }

            const formData = new FormData();
            formData.append('profile_picture', input.files[0]);

            status.textContent = "Uploading...";

            try {
                const res: Response = await fetch("/profile/upload-profile-picture", {
                    method: "POST",
                    body: formData,
                });

                interface UploadResponse {
                    error?: string;
                }
                const data: UploadResponse = await res.json();
                
                if (res.ok) {
                    await loadPFP();
                    status.textContent = "Profile picture updated successfully!";
                } else {
                    status.textContent = data.error || "Upload failed.";
                }
            } catch (err) {
                console.error(err);
                status.textContent = "An error occurred while uploading.";
            }
        });
    }
});

async function initNextAction(): Promise<void> {
    const btn = document.getElementById('next-action-btn') as HTMLButtonElement;
    const modal = document.getElementById('next-modal') as HTMLElement;
    const overlay = document.getElementById('overlay') as HTMLElement;
    const generateBtn = document.getElementById('generate-btn') as HTMLButtonElement;
    
    if (!btn || !modal || !overlay || !generateBtn) return;
    
    let currentSuggestion: NextActionSuggestion | null = null;
    
    function updateModalTheme(): void {
        const isDark: boolean = document.body.classList.contains('dark');
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
            const res: Response = await fetch('/api/next-action');
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
        const url: string = `${baseUrls[currentSuggestion.action_type] || '/quiz-generator'}?topic=${encodeURIComponent(currentSuggestion.topic)}`;
        window.location.href = url;
    });
}

class StudyStreakHeatmap {
    private container: HTMLElement | null;
    private tooltip: HTMLElement | null;
    private colorPicker: HTMLInputElement | null;
    private baseColor: string;
    private data: StreakDay[] = [];
    private maxCount: number = 0;

    constructor(containerId: string, tooltipId: string) {
        this.container = document.getElementById(containerId) as HTMLElement;
        this.tooltip = document.getElementById(tooltipId) as HTMLElement;
        this.colorPicker = document.getElementById('base-color') as HTMLInputElement;
        this.baseColor = this.loadSavedColor() || '#4aa8ff';
        
        if (this.colorPicker) {
            this.colorPicker.value = this.baseColor;
        }
        
        this.init();
        this.setupThemeObserver();
    }
    
    private setupThemeObserver(): void {
        const observer = new MutationObserver((mutations: MutationRecord[]): void => {
            mutations.forEach((mutation: MutationRecord) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    this.renderHeatmap();
                }
            });
        });
        
        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
    
    private loadSavedColor(): string | null {
        return localStorage.getItem('heatmap-color');
    }
    
    private saveColor(color: string): void {
        localStorage.setItem('heatmap-color', color);
    }
    
    private async init(): Promise<void> {
        if (!this.container) return;
        
        if (this.colorPicker) {
            this.colorPicker.addEventListener('change', (e: Event): void => {
                const target = e.target as HTMLInputElement;
                this.baseColor = target.value;
                this.saveColor(this.baseColor);
                this.renderHeatmap();
            });
        }
        
        document.querySelectorAll('.color-preset').forEach((btn: Element) => {
            btn.addEventListener('click', (e: Event): void => {
                const color = (e.target as HTMLElement).dataset.color;
                if (color) {
                    this.baseColor = color;
                    if (this.colorPicker) this.colorPicker.value = color;
                    this.saveColor(color);
                    this.renderHeatmap();
                }
            });
        });
        
        await this.fetchData();
        this.renderHeatmap();
    }
    
    private async fetchData(): Promise<void> {
        try {
            const response: Response = await fetch('/api/study-streak');
            if (!response.ok) throw new Error('Failed to fetch streak data');
            
            const result: StreakData = await response.json();
            this.data = result.data;
            this.maxCount = Math.max(...this.data.map(d => d.count), 1);
            
            const currentStreakEl = document.getElementById('current-streak') as HTMLElement;
            const longestStreakEl = document.getElementById('longest-streak') as HTMLElement;
            const totalDaysEl = document.getElementById('total-days') as HTMLElement;
            const totalActivitiesEl = document.getElementById('total-activities') as HTMLElement;
            
            if (currentStreakEl) currentStreakEl.textContent = result.currentStreak;
            if (longestStreakEl) longestStreakEl.textContent = result.longestStreak;
            if (totalDaysEl) totalDaysEl.textContent = result.totalDays;
            if (totalActivitiesEl) totalActivitiesEl.textContent = result.totalActivities; 
            
        } catch (error) {
            console.error('Error fetching streak data:', error);
        }
    }
    
    private getIntensity(count: number): number {
        if (count === 0) return 0;
        return Math.sqrt(count / this.maxCount);
    }
    
    private hexToRgb(hex: string): { r: number; g: number; b: number } | null {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    
    private getColorForIntensity(intensity: number): string {
        const isDarkTheme: boolean = document.body.classList.contains('dark');
        
        if (intensity === 0) {
            return isDarkTheme ? 'rgba(255, 255, 255, 0.08)' : '#ebedf0';
        }
        
        const rgb = this.hexToRgb(this.baseColor);
        if (!rgb) return isDarkTheme ? 'rgba(255, 255, 255, 0.08)' : '#ebedf0';
        
        if (isDarkTheme) {
            const bgR = 13, bgG = 16, bgB = 27;
            const blendedR = Math.round(bgR + (rgb.r - bgR) * intensity);
            const blendedG = Math.round(bgG + (rgb.g - bgG) * intensity);
            const blendedB = Math.round(bgB + (rgb.b - bgB) * intensity);
            return `rgb(${blendedR}, ${blendedG}, ${blendedB})`;
        } else {
            const blendedR = Math.round(255 + (rgb.r - 255) * intensity);
            const blendedG = Math.round(255 + (rgb.g - 255) * intensity);
            const blendedB = Math.round(255 + (rgb.b - 255) * intensity);
            return `rgb(${blendedR}, ${blendedG}, ${blendedB})`;
        }
    }
    
    private renderHeatmap(): void {
        if (!this.container) return;
        
        this.container.innerHTML = '';
        
        const sampleIntensities = [0, 0.25, 0.5, 0.75, 1.0];
        for (let i = 0; i <= 4; i++) {
            const legendBox = document.querySelector(`.legend-box.level-${i}`) as HTMLElement;
            if (legendBox) {
                legendBox.style.backgroundColor = this.getColorForIntensity(sampleIntensities[i]);
            }
        }
        
        const today: string = new Date().toISOString().split('T')[0];
        const firstDay: StreakDay | undefined = this.data[0];
        const firstWeekday: number = firstDay ? firstDay.weekday : 0;
        
        this.data.forEach((day: StreakDay, index: number) => {
            const cell: HTMLDivElement = document.createElement('div');
            cell.className = 'day-cell';
            
            const intensity: number = this.getIntensity(day.count);
            cell.style.backgroundColor = this.getColorForIntensity(intensity);
            cell.dataset.date = day.date;
            cell.dataset.count = day.count.toString();
            
            if (day.date === today) {
                cell.classList.add('current-day');
            }
            
            const daysSinceStart: number = index;
            const weekColumn: number = Math.floor((daysSinceStart + firstWeekday) / 7) + 1;
            const rowPosition: number = day.weekday + 1;
            
            cell.style.gridColumn = weekColumn.toString();
            cell.style.gridRow = rowPosition.toString();
            
            cell.addEventListener('mouseenter', (e: MouseEvent): void => this.showTooltip(e, day));
            cell.addEventListener('mousemove', (e: MouseEvent): void => this.updateTooltipPosition(e));
            cell.addEventListener('mouseleave', (): void => this.hideTooltip());
            
            this.container!.appendChild(cell);
        });
    }

    private updateTooltipPosition(event: MouseEvent): void {
        if (!this.tooltip || this.tooltip.style.display === 'none') return;
        
        const offsetX = -310;
        const offsetY = -30;
        
        let left: number = event.clientX + offsetX;
        let top: number = event.clientY + offsetY;
        
        const tooltipRect: DOMRect = this.tooltip.getBoundingClientRect();
        
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = event.clientX - tooltipRect.width - offsetX;
        }
        
        if (top + tooltipRect.height > window.innerHeight - 10) {
            top = event.clientY - tooltipRect.height - offsetY;
        }
        
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.top = `${top}px`;
    }

    private showTooltip(event: MouseEvent, day: StreakDay): void {
        if (!this.tooltip) return;
        
        const dateObj: Date = new Date(day.date);
        const today: string = new Date().toISOString().split('T')[0];
        const isToday: boolean = day.date === today;
        
        const formattedDate: string = dateObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        
        const dateEl = this.tooltip.querySelector('.tooltip-date') as HTMLElement;
        const countEl = this.tooltip.querySelector('.tooltip-count') as HTMLElement;
        const streakEl = this.tooltip.querySelector('.tooltip-streak') as HTMLElement;
        
        if (dateEl) {
            dateEl.textContent = isToday ? `${formattedDate} (Today)` : formattedDate;
        }
        if (countEl) {
            const activityText: string = day.count === 1 ? 'activity' : 'activities';
            countEl.textContent = `${day.count} ${activityText}`;
        }
        
        const currentStreakEl = document.getElementById('current-streak') as HTMLElement;
        if (streakEl && currentStreakEl) {
            streakEl.textContent = `Current streak: ${currentStreakEl.textContent} days`;
        }
        
        this.tooltip.style.display = 'block';
        
        const offsetX = -310;
        const offsetY = -30;
        
        let left: number = event.clientX + offsetX;
        let top: number = event.clientY + offsetY;
        
        const tooltipRect: DOMRect = this.tooltip.getBoundingClientRect();
        
        if (left < 5) left = 5;
        if (left + tooltipRect.width > window.innerWidth - 5) {
            left = window.innerWidth - tooltipRect.width - 5;
        }
        
        if (top < 5) top = 5;
        if (top + tooltipRect.height > window.innerHeight - 5) {
            top = window.innerHeight - tooltipRect.height - 5;
        }
        
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.top = `${top}px`;
    }
    
    private hideTooltip(): void {
        if (this.tooltip) {
            this.tooltip.style.display = 'none';
        }
    }
}

// Initialize everything when page loads
document.addEventListener('DOMContentLoaded', async (): Promise<void> => {
    await loadPFP();
    initNextAction();
    new StudyStreakHeatmap('heatmap', 'heatmap-tooltip');
});