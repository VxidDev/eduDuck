"use strict";
(() => {
    document.addEventListener('DOMContentLoaded', () => {
        const deleteAccountBtn = document.getElementById('delete-account-btn');
        const deleteModal = document.getElementById('delete-modal');
        const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        const deletePassword = document.getElementById('delete-password');
        const deleteConfirmCheckbox = document.getElementById('delete-confirm-checkbox');
        const deleteConfirmText = document.getElementById('delete-confirm-text');
        const deleteError = document.getElementById('delete-error');
        if (!deleteAccountBtn || !deleteModal || !cancelDeleteBtn || !confirmDeleteBtn ||
            !deletePassword || !deleteConfirmCheckbox || !deleteConfirmText || !deleteError) {
            return;
        }
        const validateDeleteForm = () => {
            const isPasswordFilled = deletePassword.value.length > 0;
            const isCheckboxChecked = deleteConfirmCheckbox.checked;
            const isTextCorrect = deleteConfirmText.value === 'DELETE';
            confirmDeleteBtn.disabled = !(isPasswordFilled && isCheckboxChecked && isTextCorrect);
        };
        deleteAccountBtn.addEventListener('click', () => {
            deleteModal.style.display = 'flex';
            deletePassword.value = '';
            deleteConfirmText.value = '';
            deleteConfirmCheckbox.checked = false;
            confirmDeleteBtn.disabled = true;
            deleteError.style.display = 'none';
        });
        cancelDeleteBtn.addEventListener('click', () => {
            deleteModal.style.display = 'none';
        });
        deletePassword.addEventListener('input', validateDeleteForm);
        deleteConfirmCheckbox.addEventListener('change', validateDeleteForm);
        deleteConfirmText.addEventListener('input', validateDeleteForm);
        confirmDeleteBtn.addEventListener('click', async () => {
            deleteError.style.display = 'none';
            confirmDeleteBtn.disabled = true;
            confirmDeleteBtn.textContent = 'Deleting...';
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                const response = await fetch('/delete-account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        password: deletePassword.value,
                        confirm: deleteConfirmText.value
                    })
                });
                const data = await response.json();
                if (response.ok) {
                    alert('Account deleted successfully. You will be redirected to the home page.');
                    window.location.href = '/';
                }
                else {
                    deleteError.textContent = data.error || 'Failed to delete account';
                    deleteError.style.display = 'block';
                    confirmDeleteBtn.disabled = false;
                    confirmDeleteBtn.textContent = 'Delete Forever';
                }
            }
            catch (error) {
                deleteError.textContent = 'Network error. Please try again.';
                deleteError.style.display = 'block';
                confirmDeleteBtn.disabled = false;
                confirmDeleteBtn.textContent = 'Delete Forever';
            }
        });
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                deleteModal.style.display = 'none';
            }
        });
    });
})();
//# sourceMappingURL=script.js.map