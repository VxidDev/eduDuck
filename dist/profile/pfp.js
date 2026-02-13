import { GetUserPFP } from "../Components/GetUserPFP.js";
export async function loadPFP() {
    const url = await GetUserPFP();
    const pfpImg = document.getElementById('user-pfp');
    if (url && pfpImg) {
        pfpImg.src = url;
    }
}
export function initPFPForm() {
    const form = document.getElementById('profile-pic-form');
    const status = document.getElementById('profile-pic-status');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('profile-picture-input');
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
                const data = await res.json();
                if (res.ok) {
                    await loadPFP();
                    status.textContent = "Profile picture updated successfully!";
                }
                else {
                    status.textContent = data.error || "Upload failed.";
                }
            }
            catch (err) {
                console.error(err);
                status.textContent = "An error occurred while uploading.";
            }
        });
    }
}
//# sourceMappingURL=pfp.js.map