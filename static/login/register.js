document.addEventListener("DOMContentLoaded", () => {
    const usernameInput = document.getElementById("username");
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const confirmInput = document.getElementById("confirm_password");
    const button = document.getElementById("register-button");
    const errorMsg = document.getElementById("register-error");

    button.addEventListener("click", async () => {
        errorMsg.style.display = "none";

        const username = usernameInput.value.trim();
        const email = emailInput.value.trim();
        const password = passwordInput.value;
        const confirm = confirmInput.value;

        if (!username || !email || !password || !confirm) {
            errorMsg.textContent = "All fields are required.";
            errorMsg.style.display = "block";
            return;
        }

        if (username.length < 4) {
            errorMsg.textContent = "Username must be at least 4 characters long.";
            errorMsg.style.display = "block";
            return;
        }

        const whitespacePattern = /\s/;
        if (whitespacePattern.test(username) || whitespacePattern.test(email) || whitespacePattern.test(password)) {
            errorMsg.textContent = "Username, email, and password cannot contain spaces.";
            errorMsg.style.display = "block";
            return;
        }

        if (password !== confirm) {
            errorMsg.textContent = "Passwords do not match.";
            errorMsg.style.display = "block";
            return;
        }

        const passwordPattern = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&()#^])(?!.*\s)[A-Za-z\d@$!%*?&()#^]{8,}$/;
        if (!passwordPattern.test(password)) {
            errorMsg.textContent = "Password must be at least 8 characters long, include letters, numbers, a special character, and no spaces.";
            errorMsg.style.display = "block";
            return;
        }

        try {
            const res = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password, confirm: confirm })
            });
            const data = await res.json();

            if (res.ok) {
                window.location.href = "/"; 
            } else {
                errorMsg.textContent = data.error || "Registration failed.";
                errorMsg.style.display = "block";
            }
        } catch (err) {
            errorMsg.textContent = "Network error. Please try again.";
            errorMsg.style.display = "block";
        }
    });
});
