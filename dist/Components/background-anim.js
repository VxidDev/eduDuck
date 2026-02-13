"use strict";
/**
 * Infinite Tri-Color Ambient Background Animation
 * Colors: Red, Blue, Orange
 * Behavior: Organic floating/drifting without mouse interaction.
 */
document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    // Configuration
    // Opacity levels for Light vs Dark mode
    const opacityLight = 0.15; // Brighter "GTA" vibe
    const opacityDark = 0.20; // Visible against black
    // Color definitions (RGB values to insert into rgba string)
    const colors = {
        red: '255, 67, 67',
        blue: '67, 83, 255',
        orange: '255, 165, 0'
    };
    // State for the 3 orbs
    // We use phases to make them move in non-synced sine waves
    const orbs = [
        { color: colors.red, phaseX: 0, phaseY: 0, speedX: 0.0003, speedY: 0.0005, radiusX: 30, radiusY: 20 },
        { color: colors.blue, phaseX: 2, phaseY: 1, speedX: 0.0004, speedY: 0.0003, radiusX: 25, radiusY: 35 },
        { color: colors.orange, phaseX: 4, phaseY: 3, speedX: 0.0002, speedY: 0.0004, radiusX: 35, radiusY: 25 }
    ];
    function animate(time) {
        // Determine current opacity based on theme
        const isDark = document.body.classList.contains('dark') ||
            document.documentElement.getAttribute('data-theme') === 'dark';
        const opacity = isDark ? opacityDark : opacityLight;
        // Calculate positions
        const gradients = orbs.map(orb => {
            // Calculate organic movement using Sine/Cosine based on time
            // Base position is roughly center-ish (30-70%) to keep them on screen
            const x = 50 + (Math.sin(time * orb.speedX + orb.phaseX) * orb.radiusX);
            const y = 50 + (Math.cos(time * orb.speedY + orb.phaseY) * orb.radiusY);
            return `radial-gradient(circle at ${x.toFixed(1)}% ${y.toFixed(1)}%, rgba(${orb.color}, ${opacity}), transparent 40%)`;
        });
        // Apply to body
        // We join them with commas to stack the gradients
        body.style.backgroundImage = gradients.join(', ');
        requestAnimationFrame(animate);
    }
    // Start loop
    requestAnimationFrame(animate);
});
//# sourceMappingURL=background-anim.js.map