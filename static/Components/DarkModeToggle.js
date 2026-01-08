const body = document.body;
const toggle = document.getElementById('theme-toggle');

if (localStorage.getItem('theme') === 'dark') {
    body.classList.add('dark');
}

toggle.addEventListener('click', () => {
    body.classList.toggle('dark');
    localStorage.setItem('theme', body.classList.contains('dark') ? 'dark' : 'light');
});