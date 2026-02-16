interface ResetPasswordResponse {
    message?: string;
    success?: boolean;
}

interface ResetPasswordRequest {
    username_email: string;
}

document.addEventListener('DOMContentLoaded', (): void => {
    const resetButton = document.getElementById('reset-button') as HTMLButtonElement;
    const usernameEmailInput = document.getElementById('username-email') as HTMLInputElement;
    const errorDisplay = document.getElementById('reset-error') as HTMLParagraphElement;
    const successDisplay = document.getElementById('reset-success') as HTMLParagraphElement;

    if (!resetButton || !usernameEmailInput || !errorDisplay || !successDisplay) {
        console.error('Required elements not found in the DOM');
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

    const setButtonLoading = (loading: boolean): void => {
        resetButton.disabled = loading;
        resetButton.textContent = loading ? 'Sending...' : 'Send Reset Link';
    };

    const handleResetPassword = async (e: Event): Promise<void> => {
        e.preventDefault();
        
        const usernameEmail: string = usernameEmailInput.value.trim();
        
        clearMessages();
        
        // Validation
        if (!usernameEmail) {
            showError('Please enter your username or email address.');
            return;
        }

        // Basic email/username validation
        if (usernameEmail.length < 3) {
            showError('Username or email must be at least 3 characters long.');
            return;
        }
        
        setButtonLoading(true);
        
        try {
            const csrfTokenElement = document.querySelector('meta[name="csrf-token"]') as HTMLMetaElement;
            
            if (!csrfTokenElement) {
                throw new Error('CSRF token not found');
            }
            
            const csrfToken: string = csrfTokenElement.getAttribute('content') || '';
            
            const requestBody: ResetPasswordRequest = {
                username_email: usernameEmail
            };
            
            const response: Response = await fetch('/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(requestBody)
            });
            
            const data: ResetPasswordResponse = await response.json();
            
            if (response.ok) {
                showSuccess(
                    data.message || 
                    'Password reset link has been sent to your email. Please check your inbox and spam folder.'
                );
                usernameEmailInput.value = '';
            } else {
                showError(
                    data.message || 
                    'An error occurred. Please try again later.'
                );
            }
        } catch (error: unknown) {
            console.error('Reset password error:', error);
            
            if (error instanceof TypeError && error.message.includes('fetch')) {
                showError('Network error. Please check your connection and try again.');
            } else if (error instanceof Error) {
                showError(error.message);
            } else {
                showError('An unexpected error occurred. Please try again.');
            }
        } finally {
            setButtonLoading(false);
        }
    };

    const handleKeyPress = (e: KeyboardEvent): void => {
        if (e.key === 'Enter') {
            resetButton.click();
        }
    };

    // Event listeners
    resetButton.addEventListener('click', handleResetPassword);
    usernameEmailInput.addEventListener('keypress', handleKeyPress);
});