export class StudyStreakHeatmap {
    constructor(containerId, tooltipId) {
        this.data = [];
        this.maxCount = 0;
        this.container = document.getElementById(containerId);
        this.tooltip = document.getElementById(tooltipId);
        this.colorPicker = document.getElementById('base-color');
        this.baseColor = this.loadSavedColor() || '#4aa8ff';
        if (this.colorPicker) {
            this.colorPicker.value = this.baseColor;
        }
        this.init();
        this.setupThemeObserver();
    }
    setupThemeObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
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
    loadSavedColor() {
        return localStorage.getItem('heatmap-color');
    }
    saveColor(color) {
        localStorage.setItem('heatmap-color', color);
    }
    async init() {
        if (!this.container)
            return;
        if (this.colorPicker) {
            this.colorPicker.addEventListener('change', (e) => {
                const target = e.target;
                this.baseColor = target.value;
                this.saveColor(this.baseColor);
                this.renderHeatmap();
            });
        }
        document.querySelectorAll('.color-preset').forEach((btn) => {
            btn.addEventListener('click', (e) => {
                const color = e.target.dataset.color;
                if (color) {
                    this.baseColor = color;
                    if (this.colorPicker)
                        this.colorPicker.value = color;
                    this.saveColor(color);
                    this.renderHeatmap();
                }
            });
        });
        await this.fetchData();
        this.renderHeatmap();
    }
    async fetchData() {
        try {
            const response = await fetch('/api/study-streak');
            if (!response.ok)
                throw new Error('Failed to fetch streak data');
            const result = await response.json();
            this.data = result.data;
            this.maxCount = Math.max(...this.data.map(d => d.count), 1);
            const currentStreakEl = document.getElementById('current-streak');
            const longestStreakEl = document.getElementById('longest-streak');
            const totalDaysEl = document.getElementById('total-days');
            const totalActivitiesEl = document.getElementById('total-activities');
            if (currentStreakEl)
                currentStreakEl.textContent = result.currentStreak;
            if (longestStreakEl)
                longestStreakEl.textContent = result.longestStreak;
            if (totalDaysEl)
                totalDaysEl.textContent = result.totalDays;
            if (totalActivitiesEl)
                totalActivitiesEl.textContent = result.totalActivities;
        }
        catch (error) {
            console.error('Error fetching streak data:', error);
        }
    }
    getIntensity(count) {
        if (count === 0)
            return 0;
        return Math.sqrt(count / this.maxCount);
    }
    hexToRgb(hex) {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result ? {
            r: parseInt(result[1], 16),
            g: parseInt(result[2], 16),
            b: parseInt(result[3], 16)
        } : null;
    }
    getColorForIntensity(intensity) {
        const isDarkTheme = document.body.classList.contains('dark');
        if (intensity === 0) {
            return isDarkTheme ? 'rgba(255, 255, 255, 0.08)' : '#ebedf0';
        }
        const rgb = this.hexToRgb(this.baseColor);
        if (!rgb)
            return isDarkTheme ? 'rgba(255, 255, 255, 0.08)' : '#ebedf0';
        if (isDarkTheme) {
            const bgR = 13, bgG = 16, bgB = 27;
            const blendedR = Math.round(bgR + (rgb.r - bgR) * intensity);
            const blendedG = Math.round(bgG + (rgb.g - bgG) * intensity);
            const blendedB = Math.round(bgB + (rgb.b - bgB) * intensity);
            return `rgb(${blendedR}, ${blendedG}, ${blendedB})`;
        }
        else {
            const blendedR = Math.round(255 + (rgb.r - 255) * intensity);
            const blendedG = Math.round(255 + (rgb.g - 255) * intensity);
            const blendedB = Math.round(255 + (rgb.b - 255) * intensity);
            return `rgb(${blendedR}, ${blendedG}, ${blendedB})`;
        }
    }
    renderHeatmap() {
        if (!this.container)
            return;
        this.container.innerHTML = '';
        const sampleIntensities = [0, 0.25, 0.5, 0.75, 1.0];
        for (let i = 0; i <= 4; i++) {
            const legendBox = document.querySelector(`.legend-box.level-${i}`);
            if (legendBox) {
                legendBox.style.backgroundColor = this.getColorForIntensity(sampleIntensities[i]);
            }
        }
        const today = new Date().toISOString().split('T')[0];
        const firstDay = this.data[0];
        const firstWeekday = firstDay ? firstDay.weekday : 0;
        this.data.forEach((day, index) => {
            const cell = document.createElement('div');
            cell.className = 'day-cell';
            const intensity = this.getIntensity(day.count);
            cell.style.backgroundColor = this.getColorForIntensity(intensity);
            cell.dataset.date = day.date;
            cell.dataset.count = day.count.toString();
            if (day.date === today) {
                cell.classList.add('current-day');
            }
            const daysSinceStart = index;
            const weekColumn = Math.floor((daysSinceStart + firstWeekday) / 7) + 1;
            const rowPosition = day.weekday + 1;
            cell.style.gridColumn = weekColumn.toString();
            cell.style.gridRow = rowPosition.toString();
            cell.addEventListener('mouseenter', (e) => this.showTooltip(e, day));
            cell.addEventListener('mousemove', (e) => this.updateTooltipPosition(e));
            cell.addEventListener('mouseleave', () => this.hideTooltip());
            this.container.appendChild(cell);
        });
    }
    updateTooltipPosition(event) {
        if (!this.tooltip || this.tooltip.style.display === 'none')
            return;
        const offsetX = -310;
        const offsetY = -30;
        let left = event.clientX + offsetX;
        let top = event.clientY + offsetY;
        const tooltipRect = this.tooltip.getBoundingClientRect();
        if (left + tooltipRect.width > window.innerWidth - 10) {
            left = event.clientX - tooltipRect.width - offsetX;
        }
        if (top + tooltipRect.height > window.innerHeight - 10) {
            top = event.clientY - tooltipRect.height - offsetY;
        }
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.top = `${top}px`;
    }
    showTooltip(event, day) {
        if (!this.tooltip)
            return;
        const dateObj = new Date(day.date);
        const today = new Date().toISOString().split('T')[0];
        const isToday = day.date === today;
        const formattedDate = dateObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
        const dateEl = this.tooltip.querySelector('.tooltip-date');
        const countEl = this.tooltip.querySelector('.tooltip-count');
        const streakEl = this.tooltip.querySelector('.tooltip-streak');
        if (dateEl) {
            dateEl.textContent = isToday ? `${formattedDate} (Today)` : formattedDate;
        }
        if (countEl) {
            const activityText = day.count === 1 ? 'activity' : 'activities';
            countEl.textContent = `${day.count} ${activityText}`;
        }
        const currentStreakEl = document.getElementById('current-streak');
        if (streakEl && currentStreakEl) {
            streakEl.textContent = `Current streak: ${currentStreakEl.textContent} days`;
        }
        this.tooltip.style.display = 'block';
        const offsetX = -310;
        const offsetY = -30;
        let left = event.clientX + offsetX;
        let top = event.clientY + offsetY;
        const tooltipRect = this.tooltip.getBoundingClientRect();
        if (left < 5)
            left = 5;
        if (left + tooltipRect.width > window.innerWidth - 5) {
            left = window.innerWidth - tooltipRect.width - 5;
        }
        if (top < 5)
            top = 5;
        if (top + tooltipRect.height > window.innerHeight - 5) {
            top = window.innerHeight - tooltipRect.height - 5;
        }
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.top = `${top}px`;
    }
    hideTooltip() {
        if (this.tooltip) {
            this.tooltip.style.display = 'none';
        }
    }
}
//# sourceMappingURL=heatmap.js.map