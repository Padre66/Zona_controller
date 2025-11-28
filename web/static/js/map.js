let tagsMeta = [];
let selectedTag = null;

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

async function drawMap() {
    const canvas = document.getElementById('map-canvas');
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#101419';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // anchorokat itt lehetne rajzolni /api/anchors alapján, most kihagyva

    const onlySelected = document.getElementById('only-selected').checked;

    if (selectedTag) {
        const pos = await fetchPosition(selectedTag);
        if (pos && pos.x !== undefined) {
            const x = canvas.width / 2 + pos.x * 10;
            const y = canvas.height / 2 - pos.y * 10;
            ctx.fillStyle = '#4caf50';
            ctx.beginPath();
            ctx.arc(x, y, 6, 0, 2 * Math.PI);
            ctx.fill();
            ctx.fillText(selectedTag, x + 8, y - 8);
        }
    }

    // ha nem csak a kiválasztottat akarjuk, itt lehetne további TAG-eket rajzolni
}

document.getElementById('tag-select').addEventListener('change', (e) => {
    selectedTag = e.target.value;
});

document.getElementById('only-selected').addEventListener('change', () => {
    // logika opcionálisan bővíthető
});

setInterval(drawMap, 1000);
loadTags().then(drawMap);
