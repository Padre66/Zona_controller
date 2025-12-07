# zona_controller/tdoa_solver/types.py

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class TDoASolveResult:
    """
    Egy TAG kiszámolt pozíciójának eredménye.

    A számítási rész később kerül implementálásra, ez csak az adatstruktúra.
    """
    tag_id: str
    x: float
    y: float
    z: float

    # meta adatok – későbbi TDoA implementációhoz hasznosak lehetnek
    used_anchors: List[str]
    # pl. anchor_id → nyers mérés / TDoA komponensek
    debug_info: Dict[str, Any]


@dataclass
class AnchorMeasurementSnapshot:
    """
    Egy anchorhoz tartozó, már előfeldolgozott mérés snapshotja
    (egy adott TAG-hez, adott időpillanat környékén).
    A konkrét mezők később bővíthetők.
    """
    anchor_id: str
    tag_id: str
    ts_recv: float
    ts_raw: Optional[int]
    uwb: Dict[str, Any]
