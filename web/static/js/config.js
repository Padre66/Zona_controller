async function loadConfig() {
    const resp = await fetch('/api/config');
    if (!resp.ok) {
        document.getElementById('config-text').value = 'Hiba /api/config híváskor';
        return;
    }
    const cfg = await resp.json();
    document.getElementById('config-text').value = JSON.stringify(cfg, null, 2);
}

async function saveConfig() {
    const text = document.getElementById('config-text').value;
    const statusSpan = document.getElementById('config-status');
    statusSpan.textContent = '';
    let json;
    try {
        json = JSON.parse(text);
    } catch (e) {
        statusSpan.textContent = 'Nem érvényes JSON.';
        return;
    }
    try {
        const resp = await fetch('/api/config', {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(json)
        });
        if (!resp.ok) {
            const data = await resp.json();
            statusSpan.textContent = 'Hiba: ' + (data.error || resp.status);
        } else {
            statusSpan.textContent = 'Mentve.';
        }
    } catch (e) {
        statusSpan.textContent = 'Hálózati hiba.';
    }
}

document.getElementById('save-config').addEventListener('click', saveConfig);

async function loadAnchors() {
    const resp = await fetch('/api/anchors');
    if (!resp.ok) return;
    const anchors = await resp.json();
    const tbody = document.querySelector('#anchor-table tbody');
    tbody.innerHTML = '';
    anchors.forEach(a => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${a.id || ''}</td>
            <td>${a.name || ''}</td>
            <td>${a.position?.x ?? ''}</td>
            <td>${a.position?.y ?? ''}</td>
            <td>${a.position?.z ?? ''}</td>
            <td>${a.enabled}</td>
        `;
        tbody.appendChild(tr);
    });
}

loadConfig();
loadAnchors();
