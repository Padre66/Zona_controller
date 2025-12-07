# zona_controller/runtime_params.py

import time
import threading
from typing import Dict, Any

from .config import ConfigManager


class TDoARuntimeParams:
    """
    TDoA-hoz kapcsolódó futás közbeni (runtime) paraméterek betöltése.

    A paraméterek a zona.conf alatt itt vannak:
        tdoa.runtime {
            expected_zone_id_hex = "0x...."
            buffer { ... }
            solver { ... }
            filter { ... }
        }

    A get_*_params() metódusok diktet adnak vissza a releváns részekkel.
    A configot 1 mp-nél gyakrabban nem tölti be újra (throttling).
    """

    def __init__(self, config_path: str = "zona.conf"):
        self._cfg_mgr = ConfigManager(config_path)
        self._lock = threading.Lock()
        self._last_load_ts = 0.0
        self._cache: Dict[str, Any] = {}

    def _reload_if_needed(self) -> None:
        now = time.time()
        # egyszerű throttling: max. 1 mp-enként olvasunk configot
        if now - self._last_load_ts < 1.0:
            return

        cfg = self._cfg_mgr.get_config()
        tdoa = cfg.get("tdoa", {})
        runtime = tdoa.get("runtime", {})

        buffer_cfg = runtime.get("buffer", {})
        solver_cfg = runtime.get("solver", {})
        filter_cfg = runtime.get("filter", {})

        # zóna filter rész
        zone_cfg = {
            "expected_zone_id_hex": runtime.get("expected_zone_id_hex", None),
        }

        # buffer paraméterek
        buffer_params = {
            "per_anchor_size": int(buffer_cfg.get("per_anchor_size", 50)),
            "max_age_sec": float(buffer_cfg.get("max_age_sec", 2.0)),
            "snapshots_per_anchor": int(buffer_cfg.get("snapshots_per_anchor", 5)),
        }

        # solver paraméterek
        solver_params = {
            "c_m_per_s": float(solver_cfg.get("c_m_per_s", 299_792_458.0)),
            "ts_unit_scale": float(solver_cfg.get("ts_unit_scale", 1.0)),
            "min_anchor_count": int(solver_cfg.get("min_anchor_count", 3)),
            "min_good_anchors": int(solver_cfg.get("min_good_anchors", 3)),
            "max_iterations": int(solver_cfg.get("max_iterations", 20)),
            "stop_threshold": float(solver_cfg.get("stop_threshold", 1e-4)),
            "max_residual_m": float(solver_cfg.get("max_residual_m", 2.0)),
            "anchor_outlier_reject_pct": float(
                solver_cfg.get("anchor_outlier_reject_pct", 0.2)
            ),
            "reference_anchor": solver_cfg.get("reference_anchor", "closest"),
            "use_lm_solver": bool(solver_cfg.get("use_lm_solver", True)),
            "enable_geometry_checks": bool(
                solver_cfg.get("enable_geometry_checks", True)
            ),
            "initial_guess": solver_cfg.get(
                "initial_guess", {"x": 0.0, "y": 0.0, "z": 0.0}
            ),
            "debug_output": bool(solver_cfg.get("debug_output", False)),
            "forward_mode": solver_cfg.get("forward_mode", "filtered"),
        }

        # filter paraméterek
        filter_params = {
            "pos_sigma_m": float(filter_cfg.get("pos_sigma_m", 0.5)),
            "process_noise": float(filter_cfg.get("process_noise", 0.1)),
            "tag_max_age_sec": float(filter_cfg.get("tag_max_age_sec", 2.0)),
            "max_jump_m": float(filter_cfg.get("max_jump_m", 5.0)),
            "velocity_damping": float(filter_cfg.get("velocity_damping", 0.8)),
        }

        with self._lock:
            self._cache = {
                "zone": zone_cfg,
                "buffer": buffer_params,
                "solver": solver_params,
                "filter": filter_params,
            }
            self._last_load_ts = now

    def get_zone_params(self) -> Dict[str, Any]:
        self._reload_if_needed()
        with self._lock:
            return dict(self._cache.get("zone", {}))

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
