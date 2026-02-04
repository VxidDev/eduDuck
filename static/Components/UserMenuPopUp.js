document.addEventListener('DOMContentLoaded', function () {
    const toggle = document.getElementById('profile-button');
    const menu = document.getElementById('user-menu');
    const wrap = document.querySelector('.user-menu-wrapper');

    function closeMenu() {
        menu.hidden = true; 
        menu.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
    }

    toggle.addEventListener('click', function (e) {
        e.stopPropagation();
        const isOpen = menu.classList.contains('open');
        if (isOpen) {
            closeMenu();
        } else {
            menu.hidden = false;
            menu.classList.add('open');
            toggle.setAttribute('aria-expanded', 'true');
        }
    });

    document.addEventListener('click', function (e) {
        if (!wrap.contains(e.target)) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeMenu();
            toggle.focus();
        }
    });
});
