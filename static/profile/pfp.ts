import { GetUserPFP } from "../Components/GetUserPFP.js";

export async function loadPFP(): Promise<void> {
    const url = await GetUserPFP();
    const pfpImg = document.getElementById('user-pfp') as HTMLImageElement;
    if (url && pfpImg) {
        pfpImg.src = url;
    }
}

export function initPFPForm(): void {
    const form = document.getElementById('profile-pic-form') as HTMLFormElement;
    const status = document.getElementById('profile-pic-status') as HTMLElement;

    if (form) {
        form.addEventListener('submit', async (e: Event): Promise<void> => {
            e.preventDefault();
            const input = document.getElementById('profile-picture-input') as HTMLInputElement;

            if (!input?.files?.length) {
                status.textContent = "Please select a file to upload.";
                return;
            }

            const formData = new FormData();
            formData.append('profile_picture', input.files[0]);

            status.textContent = "Uploading...";

            try {
                const res = await fetch("/profile/upload-profile-picture", {
                    method: "POST",
                    body: formData,
                });

                interface UploadResponse {
                    error?: string;
                }
                const data: UploadResponse = await res.json();

                if (res.ok) {
                    await loadPFP();
                    status.textContent = "Profile picture updated successfully!";
                } else {
                    status.textContent = data.error || "Upload failed.";
                }
            } catch (err) {
                console.error(err);
                status.textContent = "An error occurred while uploading.";
            }
        });
    }
}
