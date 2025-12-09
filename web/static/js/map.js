let mapConfig = null;
let anchors = [];

async function loadMapConfig() {
    const resp = await fetch('/api/tdoa/map');
    if (!resp.ok) return;
    const data = await resp.json();
    mapConfig = data;
    anchors = data.anchors || [];
}

async function loadTags() {
    const resp = await fetch('/api/tdoa/tags');
    if (!resp.ok) return;
    tagsMeta = await resp.json();
    const sel = document.getElementById('tag-select');
    sel.innerHTML = '';
    tagsMeta.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = t.id + (t.name ? ' - ' + t.name : '');
        sel.appendChild(opt);
    });
    if (tagsMeta.length > 0) {
        selectedTag = tagsMeta[0].id;
        sel.value = selectedTag;
    }
}

async function fetchPosition(tagId) {
    const resp = await fetch('/api/tdoa/position?tag_id=' + encodeURIComponent(tagId));
    if (!resp.ok) return null;
    return await resp.json();
}

function worldToCanvas(x, y, canvas) {
    if (!mapConfig) return { x: 0, y: 0 };

    const widthM = mapConfig.width_m || 10;
    const heightM = mapConfig.height_m || 10;
    const origin = mapConfig.origin || { x: 0, y: 0 };

    // skála – úgy választjuk, hogy a teljes bbox kiférjen
    const scaleX = canvas.width / widthM;
    const scaleY = canvas.height / heightM;
    const s = Math.min(scaleX, scaleY);

    const px = (x - origin.x) * s;
    // Y: világból (0 alul) → canvas (0 felül)
    const py = canvas.height - (y - origin.y) * s;

    return { x: px, y: py };
}

async function drawMap() {
    const canvas = document.getElementById('map-canvas');
    const ctx = canvas.getContext('2d');

    // háttér
    ctx.fillStyle = '#101419';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    if (!mapConfig) {
        return;
    }

    const shape = (mapConfig.shape || {});
    const vertices = shape.vertices || [];

    // zóna polygon kirajzolása, ha van
    if (vertices.length > 1) {
        ctx.beginPath();
        vertices.forEach((v, idx) => {
            const p = worldToCanvas(v.x, v.y, canvas);
            if (idx === 0) {
                ctx.moveTo(p.x, p.y);
            } else {
                ctx.lineTo(p.x, p.y);
            }
        });
        ctx.closePath();
        ctx.strokeStyle = '#3f51b5';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = 'rgba(63,81,181,0.15)';
        ctx.fill();
    }

    // anchorok
    anchors.forEach(a => {
        if (!a.position) return;
        const p = worldToCanvas(a.position.x, a.position.y, canvas);
        ctx.fillStyle = '#ff9800';
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillText(a.id || '', p.x + 6, p.y - 4);
    });

    const onlySelected = document.getElementById('only-selected').checked;

    // kiválasztott TAG
    if (selectedTag) {
        const pos = await fetchPosition(selectedTag);
        if (pos && pos.x !== undefined) {
            const p = worldToCanvas(pos.x, pos.y, canvas);
            ctx.fillStyle = '#4caf50';
            ctx.beginPath();
            ctx.arc(p.x, p.y, 6, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillText(selectedTag, p.x + 8, p.y - 8);
        }
    }

    // ha később több TAG-et is rajzolnál, itt tudod bővíteni,
    // a pos.x/pos.y-t mindig worldToCanvas-on keresztül vidd át
}

document.getElementById('tag-select').addEventListener('change', (e) => {
    selectedTag = e.target.value;
});

document.getElementById('only-selected').addEventListener('change', () => {
    // logika opcionálisan bővíthető
});

async function initMap() {
    await loadMapConfig();
    await loadTags();
    drawMap();
    setInterval(drawMap, 1000);
}

initMap();
