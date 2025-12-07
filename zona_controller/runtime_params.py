# zona_controller/runtime_params.py
import time
import threading
from typing import Dict, Any

from .config import ConfigManager

class TDoARuntimeParams:
    def __init__(self, config_path: str = "zona.conf"):
        self._cfg_mgr = ConfigManager(config_path)
        self._lock = threading.Lock()
        self._last_load_ts = 0.0
        self._cache: Dict[str, Any] = {}

    def _reload_if_needed(self):
        now = time.time()
        if now - self._last_load_ts < 1.0:
            return

        cfg = self._cfg_mgr.get_config()
        tdoa = cfg.get("tdoa", {})
        runtime = tdoa.get("runtime", {})

        buffer_cfg = runtime.get("buffer", {})
        solver_cfg = runtime.get("solver", {})
        filter_cfg = runtime.get("filter", {})

        # ÚJ: zóna filter
        zone_cfg = {
            "expected_zone_id_hex": runtime.get("expected_zone_id_hex", None),
        }

        with self._lock:
            self._cache = {
                "buffer": {
                    "per_anchor_size": int(buffer_cfg.get("per_anchor_size", 50)),
                    "max_age_sec": float(buffer_cfg.get("max_age_sec", 2.0)),
                },
                "solver": {
                    "c_m_per_s": float(solver_cfg.get("c_m_per_s", 299_792_458.0)),
                    "max_residual_m": float(solver_cfg.get("max_residual_m", 2.0)),
                    "max_iterations": int(solver_cfg.get("max_iterations", 20)),
                },
                "filter": {
                    "pos_sigma_m": float(filter_cfg.get("pos_sigma_m", 0.5)),
                    "process_noise": float(filter_cfg.get("process_noise", 0.1)),
                    "tag_max_age_sec": float(filter_cfg.get("tag_max_age_sec", 2.0)),
                },
                "zone": zone_cfg,  # <-- ÚJ
            }
            self._last_load_ts = now

    def get_buffer_params(self) -> Dict[str, Any]:
        self._reload_if_needed()
        with self._lock:
            return dict(self._cache.get("buffer", {}))

    def get_solver_params(self) -> Dict[str, Any]:
        self._reload_if_needed()
        with self._lock:
            return dict(self._cache.get("solver", {}))

    def get_filter_params(self) -> Dict[str, Any]:
        self._reload_if_needed()
        with self._lock:
            return dict(self._cache.get("filter", {}))

    def get_zone_params(self) -> Dict[str, Any]:
        self._reload_if_needed()
        with self._lock:
            return dict(self._cache.get("zone", {}))
