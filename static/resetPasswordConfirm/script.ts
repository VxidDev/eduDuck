(() => {
    document.addEventListener('DOMContentLoaded', (): void => {
        const confirmButton = document.getElementById('confirm-button') as HTMLButtonElement | null;
        const passwordInput = document.getElementById('password') as HTMLInputElement | null;
        const confirmInput = document.getElementById('confirm') as HTMLInputElement | null;
        const tokenInput = document.getElementById('token') as HTMLInputElement | null;
        const errorDisplay = document.getElementById('reset-error') as HTMLParagraphElement | null;
        const successDisplay = document.getElementById('reset-success') as HTMLParagraphElement | null;

        const reqLength = document.getElementById('req-length') as HTMLDivElement | null;
        const reqLetter = document.getElementById('req-letter') as HTMLDivElement | null;
        const reqNumber = document.getElementById('req-number') as HTMLDivElement | null;
        const reqSpecial = document.getElementById('req-special') as HTMLDivElement | null;
        const reqNoSpace = document.getElementById('req-no-space') as HTMLDivElement | null;
        const passwordMatch = document.getElementById('password-match') as HTMLDivElement | null;

        if (!confirmButton || !passwordInput || !confirmInput || !tokenInput || !errorDisplay || !successDisplay || !reqLength || !reqLetter || !reqNumber || !reqSpecial || !reqNoSpace || !passwordMatch) {
            return;
        }

        const clearMessages = (): void => {
            errorDisplay.style.display = 'none';
            successDisplay.style.display = 'none';
            errorDisplay.textContent = '';
            successDisplay.textContent = '';
        };

        const showError = (message: string): void => {
            errorDisplay.textContent = message;
            errorDisplay.style.display = 'block';
        };

        const showSuccess = (message: string): void => {
            successDisplay.textContent = message;
            successDisplay.style.display = 'block';
        };

        const checkPasswordMatch = (): void => {
            const password = passwordInput.value;
            const confirm = confirmInput.value;

            if (confirm.length > 0) {
                passwordMatch.style.display = 'flex';
                passwordMatch.classList.toggle('met', password === confirm && password.length > 0);
            } else {
                passwordMatch.style.display = 'none';
            }
        };

        passwordInput.addEventListener('input', (): void => {
            const password = passwordInput.value;

            reqLength.classList.toggle('met', password.length >= 8);
            reqLetter.classList.toggle('met', /[A-Za-z]/.test(password));
            reqNumber.classList.toggle('met', /\d/.test(password));
            reqSpecial.classList.toggle('met', /[@$!%*?&()#^]/.test(password));
            reqNoSpace.classList.toggle('met', !/\s/.test(password) && password.length > 0);

            checkPasswordMatch();
        });

        confirmInput.addEventListener('input', checkPasswordMatch);

        const handleResetConfirm = async (e: Event): Promise<void> => {
            e.preventDefault();

            const password = passwordInput.value;
            const confirm = confirmInput.value;
            const token = tokenInput.value;

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

            confirmButton.disabled = true;
            confirmButton.textContent = 'Resetting...';

            try {
                const csrfToken = (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.getAttribute('content') || '';

                const response = await fetch(`/reset-password/${token}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ password, confirm })
                });

                const data = await response.json();

                if (response.ok) {
                    showSuccess(data.message || 'Password reset successful!');
                    passwordInput.value = '';
                    confirmInput.value = '';

                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                } else {
                    showError(data.message || 'Failed to reset password.');
                }
            } catch (error) {
                showError('Network error. Please try again.');
            } finally {
                confirmButton.disabled = false;
                confirmButton.textContent = 'Reset Password';
            }
        };

        confirmButton.addEventListener('click', handleResetConfirm);

        confirmInput.addEventListener('keypress', (e: KeyboardEvent): void => {
            if (e.key === 'Enter') {
                confirmButton.click();
            }
        });
    });
})();
