document.addEventListener('DOMContentLoaded', (): void => {
    const setupButton = document.getElementById('setup-button') as HTMLButtonElement | null;
    const passwordInput = document.getElementById('password') as HTMLInputElement | null;
    const confirmInput = document.getElementById('confirm') as HTMLInputElement | null;
    const errorDisplay = document.getElementById('setup-error') as HTMLParagraphElement | null;
    const successDisplay = document.getElementById('setup-success') as HTMLParagraphElement | null;

    const reqLength = document.getElementById('req-length') as HTMLDivElement | null;
    const reqLetter = document.getElementById('req-letter') as HTMLDivElement | null;
    const reqNumber = document.getElementById('req-number') as HTMLDivElement | null;
    const reqSpecial = document.getElementById('req-special') as HTMLDivElement | null;
    const reqNoSpace = document.getElementById('req-no-space') as HTMLDivElement | null;
    const passwordMatch = document.getElementById('password-match') as HTMLDivElement | null;

    if (!setupButton || !passwordInput || !confirmInput || !errorDisplay || !successDisplay) {
        return;
    }

    if (!reqLength || !reqLetter || !reqNumber || !reqSpecial || !reqNoSpace || !passwordMatch) {
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
            if (password === confirm && password.length > 0) {
                passwordMatch.classList.add('met');
            } else {
                passwordMatch.classList.remove('met');
            }
        } else {
            passwordMatch.style.display = 'none';
        }
    };

    passwordInput.addEventListener('input', (): void => {
        const password = passwordInput.value;

        if (password.length >= 8) {
            reqLength.classList.add('met');
        } else {
            reqLength.classList.remove('met');
        }

        if (/[A-Za-z]/.test(password)) {
            reqLetter.classList.add('met');
        } else {
            reqLetter.classList.remove('met');
        }

        if (/\d/.test(password)) {
            reqNumber.classList.add('met');
        } else {
            reqNumber.classList.remove('met');
        }

        if (/[@$!%*?&()#^]/.test(password)) {
            reqSpecial.classList.add('met');
        } else {
            reqSpecial.classList.remove('met');
        }

        if (!/\s/.test(password) && password.length > 0) {
            reqNoSpace.classList.add('met');
        } else {
            reqNoSpace.classList.remove('met');
        }

        checkPasswordMatch();
    });

    confirmInput.addEventListener('input', checkPasswordMatch);

    const handleSetupPassword = async (e: Event): Promise<void> => {
        e.preventDefault();
        
        const password = passwordInput.value;
        const confirm = confirmInput.value;
        
        clearMessages();
        
        if (!password || !confirm) {
            showError('Please fill in both password fields.');
            return;
        }

        const whitespacePattern = /\s/;
        if (whitespacePattern.test(password)) {
            showError('Password cannot contain spaces.');
            return;
        }

        if (password !== confirm) {
            showError('Passwords do not match.');
            return;
        }

        const passwordPattern = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&()#^])(?!.*\s)[A-Za-z\d@$!%*?&()#^]{8,}$/;
        if (!passwordPattern.test(password)) {
            showError('Password must meet all requirements above.');
            return;
        }
        
        setupButton.disabled = true;
        setupButton.textContent = 'Setting up...';
        
        try {
            const csrfToken = (document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement)?.getAttribute('content') || '';
            
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
            } else {
                showError(data.message || 'Failed to setup password.');
            }
        } catch (error) {
            showError('Network error. Please try again.');
        } finally {
            setupButton.disabled = false;
            setupButton.textContent = 'Setup Password';
        }
    };

    setupButton.addEventListener('click', handleSetupPassword);
    
    confirmInput.addEventListener('keypress', (e: KeyboardEvent): void => {
        if (e.key === 'Enter') {
            setupButton.click();
        }
    });
});
