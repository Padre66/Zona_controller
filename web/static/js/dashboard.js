function renderNodes(nodes) {
    const container = document.getElementById('node-cards');
    if (!container) return;

    container.innerHTML = '';

    if (!nodes || nodes.length === 0) {
        const p = document.createElement('p');
        p.className = 'empty-text';
        p.textContent = 'Még nem érkezett HB / mérési csomag.';
        container.appendChild(p);
        return;
    }

    const nowSec = Date.now() / 1000;

    nodes.forEach(node => {
        const card = document.createElement('div');
        card.className = 'node-card';

        const hb = node.last_hb || null;
        const meas = node.last_meas || null;

        const hbAge = hb && hb.time ? nowSec - hb.time : null;
        const measAge = meas && meas.time ? nowSec - meas.time : null;

        let statusText = 'Nincs HB';
        let statusClass = 'node-chip node-chip-offline';

        if (hbAge != null) {
            if (hbAge < 5) {
                statusText = 'Online';
                statusClass = 'node-chip node-chip-online';
            } else {
                statusText = `HB régi (+${hbAge.toFixed(1)} s)`;
                statusClass = 'node-chip node-chip-stale';
            }
        }

        const hbText = hb && hb.decoded ? hb.decoded : '-';
        const measText = meas && meas.decoded ? meas.decoded : '-';

        const hbTimeStr = hb && hb.time ? new Date(hb.time * 1000).toLocaleTimeString() : '-';
        const measTimeStr = meas && meas.time ? new Date(meas.time * 1000).toLocaleTimeString() : '-';

        card.innerHTML = `
            <div class="node-card-header">
                <div class="node-id">${node.addr || 'ismeretlen eszköz'}</div>
                <div class="${statusClass}">${statusText}</div>
            </div>

            <div class="node-card-section">
                <div class="node-section-title">Heartbeat (HB)</div>
                <div class="node-card-row">
                    <span class="node-value-strong">${hbText}</span>
                </div>
                <div class="node-card-row">
                    <span>Idő:</span>
                    <span>${hbTimeStr}</span>
                </div>
            </div>

            <div class="node-card-section">
                <div class="node-section-title">Mérés</div>
                <div class="node-card-row">
                    <span class="node-value-strong">${measText}</span>
                </div>
                <div class="node-card-row">
                    <span>Idő:</span>
                    <span>${measTimeStr}</span>
                </div>
            </div>
        `;

        container.appendChild(card);
    });
}

async function loadStatus() {
    try {
        const resp = await fetch('/api/status');
        if (!resp.ok) {
            const el = document.getElementById('status-json');
            if (el) el.textContent = 'Hiba /api/status híváskor';
            return;
        }
        const data = await resp.json();

        // Nyers utolsó üzenet debughoz
        const lastMsgEl = document.getElementById('status-json');
        if (lastMsgEl) {
            lastMsgEl.textContent = JSON.stringify(data.last_msg, null, 2);
        }

        // Fix pont kártyák
        renderNodes(data.nodes);

        // TAG táblázat (meglevő funkció)
        const tags = data.tags || {};
        const tbody = document.querySelector('#tag-table tbody');
        if (tbody) {
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
        }
    } catch (e) {
        const el = document.getElementById('status-json');
        if (el) el.textContent = 'Hálózati hiba.';
    }
}

setInterval(loadStatus, 2000);
loadStatus();
