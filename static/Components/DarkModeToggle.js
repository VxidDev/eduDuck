const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

// Load saved theme
if (localStorage.getItem('theme') === 'dark') {
    body.classList.add('dark');
    themeToggle.textContent = '☀️';
} else {
    themeToggle.textContent = '🌙';
}

// Theme toggle with animations
themeToggle.addEventListener('click', function(e) {
    const isDark = body.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    
    // Update icon
    this.textContent = isDark ? '☀️' : '🌙';
    
    // Add flip animation
    this.classList.add('switching');
    setTimeout(() => this.classList.remove('switching'), 600);
    
    // Create ripple at click position
    const ripple = document.createElement('span');
    ripple.classList.add('ripple');
    const rect = this.getBoundingClientRect();
    ripple.style.left = `${e.clientX - rect.left}px`;
    ripple.style.top = `${e.clientY - rect.top}px`;
    this.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
    
    // Particle burst
    createParticleBurst(this);
});

function createParticleBurst(button) {
    const particleCount = 6;
    const particles = document.createElement('div');
    particles.classList.add('particles');
    button.appendChild(particles);
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('span');
        particle.classList.add('particle');
        
        const angle = (360 / particleCount) * i;
        const distance = 45;
        const duration = 500 + Math.random() * 200;
        
        particle.style.left = '50%';
        particle.style.top = '50%';
        
        particle.animate([
            {
                transform: 'translate(-50%, -50%) scale(1)',
                opacity: 1
            },
            {
                transform: `translate(-50%, -50%) translate(${Math.cos(angle * Math.PI / 180) * distance}px, ${Math.sin(angle * Math.PI / 180) * distance}px) scale(0)`,
                opacity: 0
            }
        ], {
            duration: duration,
            easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)'
        });
        
        particles.appendChild(particle);
    }
    
    setTimeout(() => particles.remove(), 700);
}

// Subtle magnetic effect
themeToggle.addEventListener('mousemove', function(e) {
    const rect = this.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    const deltaX = (e.clientX - centerX) * 0.08;
    const deltaY = (e.clientY - centerY) * 0.08;
    
    this.style.transform = `translate(${deltaX}px, ${deltaY}px) scale(1.1)`;
});

themeToggle.addEventListener('mouseleave', function() {
    this.style.transform = '';
});
