export function InitFileUploads({
    selector = '.file-input',
    wrapperSelector = '.file-upload-wrapper',
    displaySelector = '.fileButton',
    defaultText = 'No file selected',
    onRegularFile,
    onImportFile
}) {
    document.querySelectorAll(selector).forEach(input => {
        input.addEventListener('change', function() {
            const wrapper = this.closest(wrapperSelector);
            const display = wrapper?.querySelector(displaySelector);

            if (!display) return;

            if (this.files.length) {
                const names = Array.from(this.files).map(f => f.name).join(', ');
                display.textContent = names.length > 30 ? `${names.slice(0, 27)}...` : names;
                display.classList.add('has-file');

                const file = this.files[0];
                if (this.classList.contains('import')) {
                    onImportFile?.(file);
                } else {
                    onRegularFile?.(file);
                }
            } else {
                display.textContent = defaultText;
                display.classList.remove('has-file');
            }
        });
    });
}
