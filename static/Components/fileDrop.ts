interface FileDropOptions {
  onFileSelect?: (files: FileList | null, input?: HTMLInputElement) => void;
}

function initFileDrop(options: FileDropOptions = {}) {
  const wrappers = document.querySelectorAll('.file-upload-wrapper');
  
  wrappers.forEach((wrapper) => {
    const fileInput = wrapper.querySelector('input[type="file"]') as HTMLInputElement;
    if (!fileInput) return;

    let errorDiv: HTMLElement | null = null;

    const createError = () => {
      errorDiv = document.createElement('div');
      errorDiv.textContent = `Invalid format. Accepts: ${fileInput.accept}`;
      errorDiv.style.cssText = `
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        background: #ff4444; color: white; padding: 12px 20px; border-radius: 6px;
        font-size: 14px; font-weight: 500; z-index: 9999; max-width: 350px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3); text-align: center;
      `;
      document.body.appendChild(errorDiv);
    };

    const removeError = () => {
      if (errorDiv) {
        errorDiv.remove();
        errorDiv = null;
      }
    };

    let dragCounter = 0;

    const handleDragEnter = (e: Event) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter++;
      if (dragCounter === 1) wrapper.classList.add('drag-over');
    };

    const handleDragLeave = (e: Event) => {
      e.preventDefault();
      e.stopPropagation();
      dragCounter--;
      if (dragCounter === 0) wrapper.classList.remove('drag-over');
    };

    const handleDragOver = (e: Event) => {
      e.preventDefault();
      e.stopPropagation();
      (e as DragEvent).dataTransfer!.dropEffect = 'copy';
    };

    const handleDrop = (e: Event) => {
      const dragEvent = e as DragEvent;
      e.preventDefault();
      e.stopPropagation();
      wrapper.classList.remove('drag-over');
      dragCounter = 0;
      removeError();

      const files = dragEvent.dataTransfer!.files;
      if (files.length === 0) return;

      const allowedTypes = fileInput.accept.split(',').map(t => t.trim().toLowerCase());
      const validFiles = Array.from(files).filter(file => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        return allowedTypes.some(type => type.startsWith('.') ? ext === type : file.type.toLowerCase().includes(type));
      }).slice(0, 1);

      if (validFiles.length > 0) {
        const dt = new DataTransfer();
        validFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        options.onFileSelect?.(dt.files, fileInput);
      } else {
        createError();
        setTimeout(removeError, 3000);
      }
    };

    wrapper.addEventListener('dragenter', handleDragEnter, true);
    wrapper.addEventListener('dragleave', handleDragLeave, true);
    wrapper.addEventListener('dragover', handleDragOver, true);
    wrapper.addEventListener('drop', handleDrop, true);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initFileDrop({
    onFileSelect: (files, input) => {
      if (input?.classList.contains('import') && files) {
        const file = files[0];
        if (file.name.toLowerCase().endsWith('.json')) {
          const reader = new FileReader();
          reader.onload = (e) => {
            try {
              const data = JSON.parse((e.target as FileReader)?.result as string);
            } catch (err) {}
          };
          reader.readAsText(file);
        }
      }
    }
  });
});
