const StatusWrapper = document.querySelector('.status-wrapper');
const Spinner = document.querySelector('.spinner');
const StatusText = document.querySelector('.status-text');
export function showSpinner() {
    StatusWrapper.classList.remove('hidden');
    Spinner.classList.remove('hidden');
    StatusText.classList.add('hidden');
    StatusText.textContent = '';
}
export function showStatus(msg) {
    StatusWrapper.classList.remove('hidden');
    StatusText.classList.remove('hidden');
    StatusText.textContent = msg;
    Spinner.classList.add('hidden');
}
export function hideStatus() {
    StatusWrapper.classList.add('hidden');
    Spinner.classList.add('hidden');
    StatusText.classList.add('hidden');
}
//# sourceMappingURL=StatusManager.js.map