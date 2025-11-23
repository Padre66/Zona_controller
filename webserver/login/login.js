document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const errorMessage = document.getElementById("errorMessage");
    const passwordInput = document.getElementById("password");
    const togglePassword = document.getElementById("togglePassword");

    togglePassword.addEventListener("click", () => {
        const isPassword = passwordInput.type === "password";
        passwordInput.type = isPassword ? "text" : "password";
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        errorMessage.style.display = "none";

        const formData = new FormData(form);

        try {
            const response = await fetch("/api/login", {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                errorMessage.style.display = "block";
                return;
            }

            const data = await response.json();

            if (!data.success) {
                errorMessage.style.display = "block";
                return;
            }

            const role = data.role;

            if (role === "Diag") {
                window.location.href = "/webserver/User/index.html";
            } else if (role === "Admin") {
                window.location.href = "/webserver/Admin/index.html";
            } else if (role === "Superuser") {
                window.location.href = "/webserver/Superuser/index.html";
            } else {
                errorMessage.style.display = "block";
            }

        } catch (err) {
            console.error(err);
            errorMessage.textContent = "Szerverhiba történt.";
            errorMessage.style.display = "block";
        }
    });
});
