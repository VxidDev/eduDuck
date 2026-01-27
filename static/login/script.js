document.addEventListener("DOMContentLoaded", () => {
    const loginButton = document.getElementById("login-button");
    const usernameInput = document.getElementById("username");
    const passwordInput = document.getElementById("password");
    const errorMsg = document.getElementById("login-error");

    loginButton.addEventListener("click", async (e) => {
        e.preventDefault(); 
        errorMsg.style.display = "none";

        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        if (!username || !password) {
            errorMsg.textContent = "Please enter both username and password.";
            errorMsg.style.display = "block";
            return;
        }

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (!response.ok) {
                errorMsg.textContent = data.error || "Login failed. Please try again.";
                errorMsg.style.display = "block";
            } else {
                window.location.href = "/";
            }

        } catch (err) {
            console.error(err);
            errorMsg.textContent = "An error occurred. Try again later.";
            errorMsg.style.display = "block";
        }
    });
});
