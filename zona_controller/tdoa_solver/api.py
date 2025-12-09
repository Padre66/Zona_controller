# zona_controller/tdoa_solver/api.py

from typing import Dict, List, Optional

from ..state import State
from ..runtime_params import TDoARuntimeParams
from .types import TDoASolveResult, AnchorMeasurementSnapshot


def collect_anchor_snapshots_for_tag(
    state: State,
    tag_id: str,
    max_age_sec: float,
) -> Dict[str, List[AnchorMeasurementSnapshot]]:
    """
    BELÉPÉSI PONT 1 – adatgyűjtés a jelenlegi State-ből.

    Visszaadja az adott TAG-hez tartozó releváns méréseket anchoronként
    csoportosítva. A konkrét logika (pl. időzítés, max. elemszám) később
    lesz részletezve; jelenleg csak a váz.

    Jelenleg: PLACEHOLDER, üres dictet ad vissza.
    """
    # TODO: később:
    #  - végigmenni state.get_anchor_buffer(anchor_id) eredményén
    #  - filter: tag_id egyezés, időablak max_age_sec
    #  - AnchorMeasurementSnapshot objektumokká alakítás
    return {}


def solve_tdoa_for_tag(
    tag_id: str,
    anchor_measurements: Dict[str, List[AnchorMeasurementSnapshot]],
    params: TDoARuntimeParams,
) -> Optional[TDoASolveResult]:
    """
    BELÉPÉSI PONT 2 – tiszta TDoA solver.

    Ez a függvény KIZÁRÓLAG a matematikával fog foglalkozni:
      - anchor pozíciók (zona.conf → anchors)
      - TDoA/TOA → (x, y, z) multilateráció
      - hibakezelés, residual-ellenőrzés, stb.

    Most még csak a váz létezik, a tényleges TDoA megvalósítás
    később kerül ide.

    Jelenleg: mindig None-t ad vissza.
    """
    # TODO: később:
    #  - anchors beolvasása ConfigManagerből vagy params-ból
    #  - anchor_measurements → Δt/Δd → (x, y, z) számítás
    #  - TDoASolveResult(...) összeállítása
    return None


def compute_position_for_tag(
    state: State,
    tag_id: str,
    params: TDoARuntimeParams,
    now_ts: float,
) -> Optional[TDoASolveResult]:
    """
    Egyszerű, fejlesztői dummy pozíciószámítás.

    Nem végez valódi TDoA-t, csak:
      - végigmegy a zona.conf tdoa.anchors listán,
      - minden anchorhoz megnézi a State anchor-bufferét,
      - kikeresi az adott TAG-hez tartozó legfrissebb mérést egy időablakon belül,
      - csoportosítja őket 'sync' szerint,
      - a legnagyobb sync-csoport anchor pozícióinak átlagát adja vissza (x,y,z).

    Követelmény: ugyanazon sync-hez tartozó legalább 3 anchor mérés.
    """

    # 1) időablak a runtime buffer paraméterekből
    buf_cfg = params.get_buffer_params()
    max_age_sec = float(buf_cfg.get("max_age_sec", 2.0))

    # 2) anchors beolvasása a zona.conf-ból
    try:
        cfg = params._cfg_mgr.get_config()  # ConfigManager a runtime_params-ben
    except AttributeError:
        return None

    tdoa_cfg = cfg.get("tdoa", {})
    anchors_cfg = tdoa_cfg.get("anchors", [])
    if not anchors_cfg:
        return None

    tag_id_str = str(tag_id)

    # 3) per-anchor legfrissebb, időben közeli mérés az adott TAG-re
    candidates: List[tuple] = []  # (anchor_id, pos_dict, sync_val, ts_recv)

    for a in anchors_cfg:
        aid = str(a.get("id") or "").strip()
        pos = a.get("position") or {}
        if not aid or not {"x", "y", "z"} <= pos.keys():
            continue

        buf = state.get_anchor_buffer(aid)
        if not buf:
            continue

        latest = None
        for m in reversed(buf):
            if str(m.get("tag_id")) != tag_id_str:
                continue
            ts_recv = float(m.get("ts_recv", 0.0))
            if now_ts - ts_recv > max_age_sec:
                continue
            latest = m
            break

        if not latest:
            continue

        uwb = latest.get("uwb", {})
        sync_val = uwb.get("sync")
        if sync_val is None:
            continue

        candidates.append(
            (aid, pos, sync_val, float(latest.get("ts_recv", 0.0)))
        )

    if not candidates:
        return None

    # 4) Csoportosítás sync alapján – azt használjuk, amelyikhez a legtöbb anchor tartozik
    by_sync: Dict[int, List[tuple]] = {}
    for item in candidates:
        sync_val = item[2]
        by_sync.setdefault(sync_val, []).append(item)

    best_sync, group = max(by_sync.items(), key=lambda kv: len(kv[1]))

    # Legalább 3 anchor kell
    if len(group) < 3:
        return None

    # 5) Anchor pozíciók átlaga
    xs: List[float] = []
    ys: List[float] = []
    zs: List[float] = []
    used_anchors: List[str] = []

    for aid, pos, sync_val, ts in group:
        xs.append(float(pos["x"]))
        ys.append(float(pos["y"]))
        zs.append(float(pos["z"]))
        used_anchors.append(aid)

    avg_x = sum(xs) / len(xs)
    avg_y = sum(ys) / len(ys)
    avg_z = sum(zs) / len(zs)

    return TDoASolveResult(
        tag_id=tag_id_str,
        x=avg_x,
        y=avg_y,
        z=avg_z,
        used_anchors=used_anchors,
        debug_info={
            "mode": "dummy_centroid",
            "sync": best_sync,
            "anchor_count": len(used_anchors),
        },
    )
