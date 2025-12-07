let currentConfig = null;

function setVal(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = value ?? '';
}

function setNumber(id, value) {
    if (value === undefined || value === null) {
        setVal(id, '');
    } else {
        setVal(id, String(value));
    }
}

function setChecked(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    el.checked = Boolean(value);
}

function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : '';
}

function getInt(id, fallback) {
    const v = getVal(id);
    if (v === '') return fallback;
    const n = parseInt(v, 10);
    return Number.isNaN(n) ? fallback : n;
}

function getFloat(id, fallback) {
    const v = getVal(id);
    if (v === '') return fallback;
    const n = parseFloat(v);
    return Number.isNaN(n) ? fallback : n;
}

function getChecked(id) {
    const el = document.getElementById(id);
    return el ? Boolean(el.checked) : false;
}

/* ---- CONFIG BETÖLTÉSE ---- */

async function loadConfig() {
    const statusSpan = document.getElementById('config-status');
    statusSpan.textContent = '';

    const resp = await fetch('/api/config');
    if (!resp.ok) {
        statusSpan.textContent = 'Hiba /api/config híváskor';
        return;
    }

    const cfg = await resp.json();
    currentConfig = cfg;

    // system
    const system = cfg.system ?? {};
    setVal('system-zone-id', system.zone_id ?? '');
    setVal('system-environment', system.environment ?? '');

    // network
    const net = cfg.network ?? {};
    setVal('network-udp-host', net.udp_host ?? '');
    setNumber('network-udp-port', net.udp_port);
    setVal('network-http-host', net.http_host ?? '');
    setNumber('network-http-port', net.http_port);
    setVal('network-sink-host', net.sink_host ?? '');
    setNumber('network-sink-port', net.sink_port);

    // tdoa
    const tdoa = cfg.tdoa ?? {};
    setVal('tdoa-zone-name', tdoa.zone_name ?? '');

    const runtime = tdoa.runtime ?? {};
    setVal('tdoa-expected-zone-id', runtime.expected_zone_id_hex ?? '');

    const map = tdoa.map ?? {};
    setNumber('map-width-m', map.width_m);
    setNumber('map-height-m', map.height_m);
    const origin = map.origin ?? {};
    setNumber('map-origin-x', origin.x);
    setNumber('map-origin-y', origin.y);

    const buffer = runtime.buffer ?? {};
    setNumber('tdoa-buffer-per-anchor-size', buffer.per_anchor_size);
    setNumber('tdoa-buffer-max-age', buffer.max_age_sec);
    setNumber('tdoa-buffer-snapshots', buffer.snapshots_per_anchor);

    const solver = runtime.solver ?? {};
    setNumber('tdoa-solver-c', solver.c_m_per_s);
    setNumber('tdoa-solver-ts-unit-scale', solver.ts_unit_scale);
    setNumber('tdoa-solver-min-anchor-count', solver.min_anchor_count);
    setNumber('tdoa-solver-min-good-anchors', solver.min_good_anchors);
    setNumber('tdoa-solver-max-iterations', solver.max_iterations);
    setNumber('tdoa-solver-stop-threshold', solver.stop_threshold);
    setNumber('tdoa-solver-max-residual', solver.max_residual_m);
    setNumber('tdoa-solver-outlier-pct', solver.anchor_outlier_reject_pct);
    setVal('tdoa-solver-reference-anchor', solver.reference_anchor ?? '');
    setChecked('tdoa-solver-use-lm', solver.use_lm_solver ?? true);
    setChecked('tdoa-solver-geometry-checks', solver.enable_geometry_checks ?? true);

    const ig = solver.initial_guess ?? {};
    setNumber('tdoa-solver-initial-x', ig.x);
    setNumber('tdoa-solver-initial-y', ig.y);
    setNumber('tdoa-solver-initial-z', ig.z);
    setChecked('tdoa-solver-debug-output', solver.debug_output ?? false);
    setVal('tdoa-solver-forward-mode', solver.forward_mode ?? 'filtered');

    const filter = runtime.filter ?? {};
    setNumber('tdoa-filter-pos-sigma', filter.pos_sigma_m);
    setNumber('tdoa-filter-process-noise', filter.process_noise);
    setNumber('tdoa-filter-tag-max-age', filter.tag_max_age_sec);
    setNumber('tdoa-filter-max-jump', filter.max_jump_m);
    setNumber('tdoa-filter-velocity-damping', filter.velocity_damping);

    // web
    const web = cfg.web ?? {};
    setNumber('web-session-timeout', web.session_timeout_sec);
}

/* ---- CONFIG ÖSSZERAKÁSA MENTÉSHEZ ---- */

function buildConfigFromForm() {
    // induljunk a jelenlegi configból, hogy amihez nincs UI mező, az megmaradjon
    const cfg = currentConfig ? structuredClone(currentConfig) : {};

    cfg.system = cfg.system || {};
    cfg.system.zone_id = getVal('system-zone-id');
    cfg.system.environment = getVal('system-environment');

    cfg.network = cfg.network || {};
    cfg.network.udp_host = getVal('network-udp-host');
    cfg.network.udp_port = getInt('network-udp-port', 100);
    cfg.network.http_host = getVal('network-http-host');
    cfg.network.http_port = getInt('network-http-port', 51200);
    cfg.network.sink_host = getVal('network-sink-host');
    cfg.network.sink_port = getInt('network-sink-port', 6000);

    cfg.tdoa = cfg.tdoa || {};
    cfg.tdoa.zone_name = getVal('tdoa-zone-name');

    const runtime = cfg.tdoa.runtime || {};
    cfg.tdoa.runtime = runtime;

    runtime.expected_zone_id_hex = getVal('tdoa-expected-zone-id') || null;

    const map = cfg.tdoa.map || {};
    cfg.tdoa.map = map;
    map.width_m = getFloat('map-width-m', map.width_m ?? 20.0);
    map.height_m = getFloat('map-height-m', map.height_m ?? 10.0);
    map.origin = map.origin || {};
    map.origin.x = getFloat('map-origin-x', map.origin.x ?? 0.0);
    map.origin.y = getFloat('map-origin-y', map.origin.y ?? 0.0);

    const buffer = runtime.buffer || {};
    runtime.buffer = buffer;
    buffer.per_anchor_size = getInt('tdoa-buffer-per-anchor-size', buffer.per_anchor_size ?? 50);
    buffer.max_age_sec = getFloat('tdoa-buffer-max-age', buffer.max_age_sec ?? 2.0);
    buffer.snapshots_per_anchor = getInt('tdoa-buffer-snapshots', buffer.snapshots_per_anchor ?? 5);

    const solver = runtime.solver || {};
    runtime.solver = solver;
    solver.c_m_per_s = getFloat('tdoa-solver-c', solver.c_m_per_s ?? 299792458.0);
    solver.ts_unit_scale = getFloat('tdoa-solver-ts-unit-scale', solver.ts_unit_scale ?? 1.0);
    solver.min_anchor_count = getInt('tdoa-solver-min-anchor-count', solver.min_anchor_count ?? 3);
    solver.min_good_anchors = getInt('tdoa-solver-min-good-anchors', solver.min_good_anchors ?? 3);
    solver.max_iterations = getInt('tdoa-solver-max-iterations', solver.max_iterations ?? 20);
    solver.stop_threshold = getFloat('tdoa-solver-stop-threshold', solver.stop_threshold ?? 1e-4);
    solver.max_residual_m = getFloat('tdoa-solver-max-residual', solver.max_residual_m ?? 2.0);
    solver.anchor_outlier_reject_pct = getFloat('tdoa-solver-outlier-pct', solver.anchor_outlier_reject_pct ?? 0.2);
    solver.reference_anchor = getVal('tdoa-solver-reference-anchor') || 'closest';
    solver.use_lm_solver = getChecked('tdoa-solver-use-lm');
    solver.enable_geometry_checks = getChecked('tdoa-solver-geometry-checks');

    const ig = solver.initial_guess || {};
    solver.initial_guess = ig;
    ig.x = getFloat('tdoa-solver-initial-x', ig.x ?? 0.0);
    ig.y = getFloat('tdoa-solver-initial-y', ig.y ?? 0.0);
    ig.z = getFloat('tdoa-solver-initial-z', ig.z ?? 0.0);

    solver.debug_output = getChecked('tdoa-solver-debug-output');
    solver.forward_mode = getVal('tdoa-solver-forward-mode') || 'filtered';

    const filter = runtime.filter || {};
    runtime.filter = filter;
    filter.pos_sigma_m = getFloat('tdoa-filter-pos-sigma', filter.pos_sigma_m ?? 0.5);
    filter.process_noise = getFloat('tdoa-filter-process-noise', filter.process_noise ?? 0.1);
    filter.tag_max_age_sec = getFloat('tdoa-filter-tag-max-age', filter.tag_max_age_sec ?? 2.0);
    filter.max_jump_m = getFloat('tdoa-filter-max-jump', filter.max_jump_m ?? 5.0);
    filter.velocity_damping = getFloat('tdoa-filter-velocity-damping', filter.velocity_damping ?? 0.8);

    cfg.web = cfg.web || {};
    cfg.web.session_timeout_sec = getInt('web-session-timeout', cfg.web.session_timeout_sec ?? 1800);

    return cfg;
}

/* ---- MENTÉS ---- */

async function saveConfig() {
    const statusSpan = document.getElementById('config-status');
    statusSpan.textContent = '';

    if (!currentConfig) {
        statusSpan.textContent = 'Config még nem töltődött be.';
        return;
    }

    const cfgToSave = buildConfigFromForm();

    try {
        const resp = await fetch('/api/config', {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(cfgToSave)
        });
        if (!resp.ok) {
            let msg = 'Ismeretlen hiba.';
            try {
                const data = await resp.json();
                msg = data.error || resp.status;
            } catch (_) {
                msg = resp.status;
            }
            statusSpan.textContent = 'Hiba: ' + msg;
        } else {
            statusSpan.textContent = 'Mentve.';
            // frissítsük a lokális currentConfig-ot is
            currentConfig = cfgToSave;
        }
    } catch (e) {
        statusSpan.textContent = 'Hálózati hiba.';
    }
}

document.getElementById('save-config').addEventListener('click', saveConfig);

/* ---- ANCHORS LISTA ---- */

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
            <td>${a.addr || ''}</td>
        `;
        tbody.appendChild(tr);
    });
}

/* ---- INIT ---- */

loadConfig();
loadAnchors();
