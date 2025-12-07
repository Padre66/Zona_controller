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
    FŐ BELÉPÉSI PONT A KÜLSŐ VILÁG SZÁMÁRA.

    Ezt fogja hívni a TDoAProcessor (vagy más réteg), ha egy TAG-hez
    pozíciót akar számolni.

    Lépések (később részletezve):
      1) anchor→TAG mérések kigyűjtése a State-ből (collect_anchor_snapshots_for_tag)
      2) TDoA számítás (solve_tdoa_for_tag)
      3) eredmény visszaadása TDoASolveResult formában
    """
    # runtime paraméterekből max_age_sec
    buf_cfg = params.get_buffer_params()
    max_age_sec = float(buf_cfg.get("max_age_sec", 2.0))

    # 1) snapshotok gyűjtése – egyelőre placeholder (üres dict)
    anchor_meas = collect_anchor_snapshots_for_tag(
        state=state,
        tag_id=tag_id,
        max_age_sec=max_age_sec,
    )

    if not anchor_meas:
        # nincs elég adat a számításhoz
        return None

    # 2) TDoA solver – jelenleg még csak váz, None-t ad vissza
    result = solve_tdoa_for_tag(tag_id, anchor_meas, params)
    return result
