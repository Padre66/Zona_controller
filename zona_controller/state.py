import threading
import time
from collections import deque
from typing import Any, Dict, Optional, List, Deque


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
        # TAG pozíciók (meglevő funkció)
        self._tag_positions: Dict[str, Dict[str, Any]] = {}
        # ÚJ: fix pontok (forrás IP:port alapján)
        # { "addr": "ip:port", "last_hb": {...}, "last_meas": {...} }
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._anchor_buffers: Dict[str, Deque[Dict[str, Any]]] = {}
        self._anchor_buffer_size = 50  # később configból

    def set_anchor_buffer_size(self, size: int):
        with self._lock:
            self._anchor_buffer_size = max(1, size)
            # meglévő bufferek maxlen frissítése
            for aid, buf in self._anchor_buffers.items():
                new_buf = deque(buf, maxlen=self._anchor_buffer_size)
                self._anchor_buffers[aid] = new_buf

    def add_anchor_measurement(self, anchor_id: str, measurement: Dict[str, Any]):
        from collections import deque
        with self._lock:
            buf = self._anchor_buffers.get(anchor_id)
            if buf is None:
                buf = deque(maxlen=self._anchor_buffer_size)
                self._anchor_buffers[anchor_id] = buf
            buf.append(measurement)

    def get_anchor_buffer(self, anchor_id: str):
        with self._lock:
            buf = self._anchor_buffers.get(anchor_id)
            if not buf:
                return []
            return list(buf)

    def update_last_message(self, addr, data: bytes, decoded: Optional[str], mode: Optional[str]):
        ts = time.time()
        addr_str = f"{addr[0]}:{addr[1]}"

        with self._lock:
            # meglevő globális utolsó üzenet
            self._last_msg["time"] = ts
            self._last_msg["from"] = addr_str
            self._last_msg["raw_len"] = len(data)
            self._last_msg["raw_hex"] = data.hex()
            self._last_msg["decoded"] = decoded
            self._last_msg["mode"] = mode

            # ÚJ: node (fix pont) szintű info
            if decoded:
                node = self._nodes.get(addr_str)
                if not node:
                    node = {
                        "addr": addr_str,
                        "last_hb": None,
                        "last_meas": None,
                    }
                    self._nodes[addr_str] = node

                # HB sor vagy mérés?
                text = decoded.strip()
                kind = None
                if text.startswith(("HB", "HB:", "HB ")):
                    kind = "hb"
                else:
                    kind = "meas"

                entry = {
                    "time": ts,
                    "raw_len": len(data),
                    "raw_hex": data.hex(),
                    "decoded": decoded,
                    "mode": mode,
                }

                if kind == "hb":
                    node["last_hb"] = entry
                elif kind == "meas":
                    node["last_meas"] = entry

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

    # ÚJ: összefoglaló a fix pontokról – Dashboard kártyákhoz
    def get_nodes_summary(self) -> List[Dict[str, Any]]:
        with self._lock:
            result: List[Dict[str, Any]] = []
            for addr, node in self._nodes.items():
                item: Dict[str, Any] = {"addr": addr}
                if node.get("last_hb"):
                    item["last_hb"] = dict(node["last_hb"])
                if node.get("last_meas"):
                    item["last_meas"] = dict(node["last_meas"])
                result.append(item)
            return result
