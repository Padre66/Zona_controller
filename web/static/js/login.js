document.getElementById('login-btn').addEventListener('click', async () => {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('login-error');

    errorDiv.textContent = '';

    try {
        const resp = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });
        const data = await resp.json();
        if (!resp.ok || !data.ok) {
            errorDiv.textContent = 'Hibás felhasználónév vagy jelszó.';
        } else {
            window.location.href = '/';
        }
    } catch (e) {
        errorDiv.textContent = 'Hálózati hiba.';
    }
});
