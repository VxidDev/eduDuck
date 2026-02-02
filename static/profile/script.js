import { GetUserPFP } from "/static/Components/getUserPFP.js"

async function loadPFP() {
    const url = await GetUserPFP();

    if (url) {
        document.getElementById('user-pfp').src = url;
    }
}

const form = document.getElementById('profile-pic-form');
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('profile-picture-input');
    const status = document.getElementById('profile-pic-status');

    if (!input.files.length) {
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
        } else {
            status.textContent = data.error || "Upload failed.";
        }
    } catch (err) {
        console.error(err);
        status.textContent = "An error occurred while uploading.";
    }
});