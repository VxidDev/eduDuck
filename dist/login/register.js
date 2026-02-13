"use strict";
(() => {
    document.addEventListener("DOMContentLoaded", () => {
        const usernameInput = document.getElementById("username");
        const emailInput = document.getElementById("email");
        const passwordInput = document.getElementById("password");
        const confirmInput = document.getElementById("confirm_password");
        const button = document.getElementById("register-button");
        const errorMsg = document.getElementById("register-error");
        const reqLength = document.getElementById("req-length");
        const reqLetter = document.getElementById("req-letter");
        const reqNumber = document.getElementById("req-number");
        const reqSpecial = document.getElementById("req-special");
        const reqNoSpace = document.getElementById("req-no-space");
        const passwordMatch = document.getElementById("password-match");
        const checkPasswordMatch = () => {
            const password = passwordInput.value;
            const confirm = confirmInput.value;
            if (confirm.length > 0) {
                passwordMatch.style.display = "flex";
                if (password === confirm && password.length > 0) {
                    passwordMatch.classList.add("met");
                }
                else {
                    passwordMatch.classList.remove("met");
                }
            }
            else {
                passwordMatch.style.display = "none";
            }
        };
        passwordInput.addEventListener("input", () => {
            const password = passwordInput.value;
            reqLength.classList.toggle("met", password.length >= 8);
            reqLetter.classList.toggle("met", /[A-Za-z]/.test(password));
            reqNumber.classList.toggle("met", /\d/.test(password));
            reqSpecial.classList.toggle("met", /[@$!%*?&()#^]/.test(password));
            reqNoSpace.classList.toggle("met", !/\s/.test(password) && password.length > 0);
            checkPasswordMatch();
        });
        confirmInput.addEventListener("input", checkPasswordMatch);
        button.addEventListener("click", async (e) => {
            e.preventDefault();
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
                errorMsg.textContent = "Password must meet all requirements above.";
                errorMsg.style.display = "block";
                return;
            }
            try {
                const res = await fetch("/register", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username, email, password, confirm })
                });
                const data = await res.json();
                if (res.ok) {
                    const redirectUrl = data.redirect || "/";
                    window.location.href = redirectUrl;
                }
                else {
                    errorMsg.textContent = data.error || "Registration failed.";
                    errorMsg.style.display = "block";
                }
            }
            catch (err) {
                errorMsg.textContent = "Network error. Please try again.";
                errorMsg.style.display = "block";
            }
        });
    });
})();
//# sourceMappingURL=register.js.map