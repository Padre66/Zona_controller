import threading
import time
from typing import Any, Dict, Optional


class State:
    def __init__(self):
        self._lock = threading.Lock()
        self._last_msg: Dict[str, Any] = {
            "time": None,
            "from": None,
            "raw_len": 0,
            "raw_hex": "",
            "decoded": None,
            "mode": None,
        }
        self._tag_positions: Dict[str, Dict[str, Any]] = {}

    def update_last_message(self, addr, data: bytes, decoded: Optional[str], mode: Optional[str]):
        ts = time.time()
        with self._lock:
            self._last_msg["time"] = ts
            self._last_msg["from"] = f"{addr[0]}:{addr[1]}"
            self._last_msg["raw_len"] = len(data)
            self._last_msg["raw_hex"] = data.hex()
            self._last_msg["decoded"] = decoded
            self._last_msg["mode"] = mode

    def get_last_message(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._last_msg)

    def update_tag_position(self, tag_id: str, x: float, y: float, z: float, ts: float):
        with self._lock:
            self._tag_positions[tag_id] = {"x": x, "y": y, "z": z, "time": ts}

    def get_tag_position(self, tag_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._tag_positions.get(tag_id)

    def get_all_tag_positions(self):
        with self._lock:
            return dict(self._tag_positions)
