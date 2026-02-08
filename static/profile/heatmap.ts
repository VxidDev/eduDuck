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

export class StudyStreakHeatmap {
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
