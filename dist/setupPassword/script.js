"use strict";
(() => {
    document.addEventListener('DOMContentLoaded', () => {
        const setupButton = document.getElementById('setup-button');
        const passwordInput = document.getElementById('password');
        const confirmInput = document.getElementById('confirm');
        const errorDisplay = document.getElementById('setup-error');
        const successDisplay = document.getElementById('setup-success');
        const reqLength = document.getElementById('req-length');
        const reqLetter = document.getElementById('req-letter');
        const reqNumber = document.getElementById('req-number');
        const reqSpecial = document.getElementById('req-special');
        const reqNoSpace = document.getElementById('req-no-space');
        const passwordMatch = document.getElementById('password-match');
        if (!setupButton || !passwordInput || !confirmInput || !errorDisplay || !successDisplay || !reqLength || !reqLetter || !reqNumber || !reqSpecial || !reqNoSpace || !passwordMatch) {
            return;
        }
        const clearMessages = () => {
            errorDisplay.style.display = 'none';
            successDisplay.style.display = 'none';
            errorDisplay.textContent = '';
            successDisplay.textContent = '';
        };
        const showError = (message) => {
            errorDisplay.textContent = message;
            errorDisplay.style.display = 'block';
        };
        const showSuccess = (message) => {
            successDisplay.textContent = message;
            successDisplay.style.display = 'block';
        };
        const checkPasswordMatch = () => {
            const password = passwordInput.value;
            const confirm = confirmInput.value;
            if (confirm.length > 0) {
                passwordMatch.style.display = 'flex';
                passwordMatch.classList.toggle('met', password === confirm && password.length > 0);
            }
            else {
                passwordMatch.style.display = 'none';
            }
        };
        passwordInput.addEventListener('input', () => {
            const password = passwordInput.value;
            reqLength.classList.toggle('met', password.length >= 8);
            reqLetter.classList.toggle('met', /[A-Za-z]/.test(password));
            reqNumber.classList.toggle('met', /\d/.test(password));
            reqSpecial.classList.toggle('met', /[@$!%*?&()#^]/.test(password));
            reqNoSpace.classList.toggle('met', !/\s/.test(password) && password.length > 0);
            checkPasswordMatch();
        });
        confirmInput.addEventListener('input', checkPasswordMatch);
        const handleSetupPassword = async (e) => {
            e.preventDefault();
            const password = passwordInput.value;
            const confirm = confirmInput.value;
            clearMessages();
            if (!password || !confirm) {
                showError('Please fill in both password fields.');
                return;
            }
            if (/\s/.test(password)) {
                showError('Password cannot contain spaces.');
                return;
            }
            if (password !== confirm) {
                showError('Passwords do not match.');
                return;
            }
            if (!/^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&()#^])(?!.*\s)[A-Za-z\d@$!%*?&()#^]{8,}$/.test(password)) {
                showError('Password must meet all requirements above.');
                return;
            }
            setupButton.disabled = true;
            setupButton.textContent = 'Setting up...';
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                const response = await fetch('/setup-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ password, confirm })
                });
                const data = await response.json();
                if (response.ok) {
                    showSuccess(data.message || 'Password setup successful!');
                    passwordInput.value = '';
                    confirmInput.value = '';
                    setTimeout(() => {
                        window.location.href = data.redirect || '/';
                    }, 1500);
                }
                else {
                    showError(data.message || 'Failed to setup password.');
                }
            }
            catch (error) {
                showError('Network error. Please try again.');
            }
            finally {
                setupButton.disabled = false;
                setupButton.textContent = 'Setup Password';
            }
        };
        setupButton.addEventListener('click', handleSetupPassword);
        confirmInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                setupButton.click();
            }
        });
    });
})();
//# sourceMappingURL=script.js.map