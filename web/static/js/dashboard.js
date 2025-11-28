async function loadStatus() {
    try {
        const resp = await fetch('/api/status');
        if (!resp.ok) {
            document.getElementById('status-json').textContent = 'Hiba /api/status híváskor';
            return;
        }
        const data = await resp.json();
        document.getElementById('status-json').textContent =
            JSON.stringify(data.last_msg, null, 2);

        const tags = data.tags || {};
        const tbody = document.querySelector('#tag-table tbody');
        tbody.innerHTML = '';
        Object.keys(tags).forEach(tagId => {
            const p = tags[tagId];
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${tagId}</td>
                <td>${p.x?.toFixed?.(3) ?? ''}</td>
                <td>${p.y?.toFixed?.(3) ?? ''}</td>
                <td>${p.z?.toFixed?.(3) ?? ''}</td>
                <td>${new Date(p.time * 1000).toLocaleString()}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        document.getElementById('status-json').textContent = 'Hálózati hiba.';
    }
}

setInterval(loadStatus, 2000);
loadStatus();
