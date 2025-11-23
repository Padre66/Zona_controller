function togglePwd() {
    const inp = document.getElementById('pwd');
    const eye = document.getElementById('eyeIcon');

    if (inp.type === 'password') {
        inp.type = 'text';
        eye.innerHTML = `
          <path d="M12 5C7 5 2.73 8.11 1 12c1.73 3.89 6 7 11 7s9.27-3.11 11-7c-1.73-3.89-6-7-11-7Z"/>
          <circle cx="12" cy="12" r="2.5"/>
          <line x1="3" y1="3" x2="21" y2="21" stroke="currentColor" stroke-width="2"/>
        `;
    } else {
        inp.type = 'password';
        eye.innerHTML = `
          <path d="M12 5C7 5 2.73 8.11 1 12c1.73 3.89 6 7 11 7s9.27-3.11 11-7c-1.73-3.89-6-7-11-7Z"/>
          <circle cx="12" cy="12" r="2.5"/>
        `;
    }
}

async function loadStatus() {
    try {
        const r = await fetch('/api/status', { cache: 'no-store' });
        if (!r.ok) throw new Error();
        const s = await r.json();

        // jelenlegi backend: { status:"ok", last_msg:{ time, decoded, ... } }
        const last = s.last_msg || {};
        const now = Date.now() / 1000;
        const last_s = last.time ? Math.max(now - last.time, 0) : NaN;

        const state = (s.status === 'ok' && last.decoded) ? 'ok' : 'off';
        const cls = state === 'ok' ? 'ok' : (state === 'warn' ? 'warn' : 'off');

        document.getElementById('status-body').innerHTML =
            `<tr>
                <td><span class="dot ${cls}"></span>A1</td>
                <td>1</td>
                <td>${Number.isFinite(last_s) ? last_s.toFixed(2) : '-'}</td>
                <td>-</td>
              </tr>`;
    } catch (e) {
        document.getElementById('status-body').innerHTML =
            `<tr><td colspan="4" class="sub">Nem érhető el az állapot.</td></tr>`;
    }
}

async function login() {
    const user = document.getElementById('user').value.trim();
    const pass = document.getElementById('pwd').value;
    const msg = document.getElementById('msg');
    msg.textContent = '';

    if (!user || !pass) {
        msg.textContent = 'Add meg a felhasználónevet és jelszót.';
        return;
    }

    try {
        // FastAPI: @app.post("/api/login"), username/password Form(...) mezőkkel
        const formData = new FormData();
        formData.append('username', user);
        formData.append('password', pass);

        const r = await fetch('/api/login', {
            method: 'POST',
            body: formData
        });

        if (!r.ok) {
            msg.textContent = 'Hibás felhasználónév vagy jelszó.';
            return;
        }

        const data = await r.json();
        const role = data.role;

        if (role === 'Diag') {
            window.location.href = '/webserver/User/index.html';
        } else if (role === 'Admin') {
            window.location.href = '/webserver/Admin/index.html';
        } else if (role === 'Superuser') {
            window.location.href = '/webserver/Superuser/index.html';
        } else {
            msg.textContent = 'Ismeretlen szerepkör.';
        }
    } catch (e) {
        console.error(e);
        msg.textContent = 'Hálózati hiba.';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('pwdToggle').addEventListener('click', togglePwd);
    document.getElementById('loginBtn').addEventListener('click', login);
    loadStatus();
    setInterval(loadStatus, 4000);
});
