document.addEventListener("DOMContentLoaded", () => {
    const usernameInput = document.getElementById("username") as HTMLInputElement;
    const emailInput = document.getElementById("email") as HTMLInputElement;
    const passwordInput = document.getElementById("password") as HTMLInputElement;
    const confirmInput = document.getElementById("confirm_password") as HTMLInputElement;
    const button = document.getElementById("register-button") as HTMLButtonElement;
    const errorMsg = document.getElementById("register-error") as HTMLElement;

    const reqLength = document.getElementById("req-length") as HTMLElement;
    const reqLetter = document.getElementById("req-letter") as HTMLElement;
    const reqNumber = document.getElementById("req-number") as HTMLElement;
    const reqSpecial = document.getElementById("req-special") as HTMLElement;
    const reqNoSpace = document.getElementById("req-no-space") as HTMLElement;
    const passwordMatch = document.getElementById("password-match") as HTMLElement;

    passwordInput.addEventListener("input", () => {
        const password: string = passwordInput.value;

        // Length requirement
        if (password.length >= 8) {
            reqLength.classList.add("met");
        } else {
            reqLength.classList.remove("met");
        }

        // Letter requirement
        if (/[A-Za-z]/.test(password)) {
            reqLetter.classList.add("met");
        } else {
            reqLetter.classList.remove("met");
        }

        // Number requirement
        if (/\d/.test(password)) {
            reqNumber.classList.add("met");
        } else {
            reqNumber.classList.remove("met");
        }

        // Special character requirement
        if (/[@$!%*?&()#^]/.test(password)) {
            reqSpecial.classList.add("met");
        } else {
            reqSpecial.classList.remove("met");
        }

        // No spaces requirement
        if (!/\s/.test(password) && password.length > 0) {
            reqNoSpace.classList.add("met");
        } else {
            reqNoSpace.classList.remove("met");
        }

        checkPasswordMatch();
    });

    confirmInput.addEventListener("input", checkPasswordMatch);

    function checkPasswordMatch(): void {
        const password: string = passwordInput.value;
        const confirm: string = confirmInput.value;

        if (confirm.length > 0) {
            passwordMatch.style.display = "flex";
            if (password === confirm && password.length > 0) {
                passwordMatch.classList.add("met");
            } else {
                passwordMatch.classList.remove("met");
            }
        } else {
            passwordMatch.style.display = "none";
        }
    }

    button.addEventListener("click", async (e: MouseEvent): Promise<void> => {
        e.preventDefault();
        errorMsg.style.display = "none";

        const username: string = usernameInput.value.trim();
        const email: string = emailInput.value.trim();
        const password: string = passwordInput.value;
        const confirm: string = confirmInput.value;

        // Required fields validation
        if (!username || !email || !password || !confirm) {
            errorMsg.textContent = "All fields are required.";
            errorMsg.style.display = "block";
            return;
        }

        // Username length validation
        if (username.length < 4) {
            errorMsg.textContent = "Username must be at least 4 characters long.";
            errorMsg.style.display = "block";
            return;
        }

        // Whitespace validation
        const whitespacePattern: RegExp = /\s/;
        if (whitespacePattern.test(username) || whitespacePattern.test(email) || whitespacePattern.test(password)) {
            errorMsg.textContent = "Username, email, and password cannot contain spaces.";
            errorMsg.style.display = "block";
            return;
        }

        // Password match validation
        if (password !== confirm) {
            errorMsg.textContent = "Passwords do not match.";
            errorMsg.style.display = "block";
            return;
        }

        // Password pattern validation
        const passwordPattern: RegExp = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&()#^])(?!.*\s)[A-Za-z\d@$!%*?&()#^]{8,}$/;
        if (!passwordPattern.test(password)) {
            errorMsg.textContent = "Password must meet all requirements above.";
            errorMsg.style.display = "block";
            return;
        }

        try {
            const res: Response = await fetch("/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ username, email, password, confirm })
            });
            
            const data: { redirect?: string; error?: string } = await res.json();

            if (res.ok) {
                const redirectUrl: string = data.redirect || "/";
                window.location.href = redirectUrl;
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
