from typing import Dict, Tuple, Optional, Any

from .state import State
from .runtime_params import TDoARuntimeParams
from .uwb_parser import parse_uwb_header

class KalmanFilter2D:
    """
    Egyszerű 2D állandó sebességű Kalman szűrő.
    Állapot: [x, y, vx, vy]^T
    """
    def __init__(self, x0=0.0, y0=0.0, vx0=0.0, vy0=0.0,
                 pos_var=1.0, vel_var=1.0, meas_var=1.0):
        import numpy as np

        self.np = np
        self.x = np.array([[x0], [y0], [vx0], [vy0]], dtype=float)
        self.P = np.eye(4) * 1000.0
        self.last_t = None
        self.pos_var = pos_var
        self.vel_var = vel_var
        self.meas_var = meas_var

    def predict(self, dt: float):
        np = self.np
        F = np.array([[1, 0, dt, 0],
                      [0, 1, 0, dt],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1]], dtype=float)
        q = self.pos_var
        Q = np.eye(4) * q
        self.x = F @ self.x
        self.P = F @ self.P @ F.T + Q

    def update(self, z: Tuple[float, float]):
        np = self.np
        H = np.array([[1, 0, 0, 0],
                      [0, 1, 0, 0]], dtype=float)
        R = np.eye(2) * self.meas_var
        z_vec = np.array([[z[0]], [z[1]]], dtype=float)
        y = z_vec - (H @ self.x)
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K @ y
        I = np.eye(4)
        self.P = (I - K @ H) @ self.P

    def step(self, t: float, z: Tuple[float, float]):
        if self.last_t is None:
            self.last_t = t
        dt = max(t - self.last_t, 1e-3)
        self.predict(dt)
        self.update(z)
        self.last_t = t

    def get_state(self) -> Tuple[float, float, float, float]:
        return tuple(v[0] for v in self.x)


class TDoAProcessor:
    """
    Erősen egyszerűsített TDoA feldolgozó:
    Feltételezi, hogy a dekódolt sorok formája:
      "TAG:<id>,X:<x>,Y:<y>,Z:<z>"
    Itt lehet később kiegészíteni valódi TDoA matematikával.
    """
    def __init__(self, state: State, params: TDoARuntimeParams):
        self.state = state
        self.params = params
        self.filters: Dict[str, KalmanFilter2D] = {}

    def _zone_matches(self, uwb: Dict[str, Any]) -> bool:
        zone_cfg = self.params.get_zone_params()
        expected_hex = zone_cfg.get("expected_zone_id_hex")
        if not expected_hex:
            # nincs konfigurálva zóna filter → mindent engedünk
            return True
        z = uwb.get("zone_id_hex")
        return z == expected_hex

    def parse_message(self, decoded: str) -> Optional[Tuple[str, float, float, float]]:
        """
        Pozíció sor parser.
        Elvárt forma (case-insensitive kulcsok):
            TAG:<id>,X:<x>,Y:<y>,Z:<z>,...

        Extra mezőket ignoráljuk.
        """
        try:
            parts = decoded.split(",")
            kv = {}
            for p in parts:
                p = p.strip()
                if ":" not in p:
                    continue
                k, v = p.split(":", 1)
                kv[k.strip().upper()] = v.strip()

            tag_id = kv.get("TAG")
            if not tag_id:
                return None

            x = float(kv.get("X", "0"))
            y = float(kv.get("Y", "0"))
            z = float(kv.get("Z", "0"))

            return tag_id, x, y, z
        except Exception:
            return None

    def update_from_message(self, decoded: str, ts_recv: float):
        """
        decoded: teljes dekódolt szöveg (lehet több sor is).
        ts_recv: fogadás időbélyege (time.time()).
        """
        for line in decoded.splitlines():
            line = line.strip()
            if not line:
                continue

            uwb = parse_uwb_header(line)
            if uwb is None:
                # nem UWB sor – ha kell, itt később kezelheted a régi TAG:X,Y,Z formátumot
                continue

            # zóna-szűrés
            if not self._zone_matches(uwb):
                continue

            anchor_id = uwb.get("anchor_hex") or uwb.get("anchor_id")
            tag_id = uwb.get("tag_hex") or uwb.get("tag_id")
            ts_raw = uwb.get("ts_raw")

            if not anchor_id or tag_id is None:
                continue

            meas: Dict[str, Any] = {
                "ts_recv": ts_recv,
                "ts_raw": ts_raw,
                "tag_id": tag_id,
                "uwb": uwb,
            }

            # anchore-onkénti buffer
            self.state.add_anchor_measurement(str(anchor_id), meas)

            # IDE jön majd később a TDoA solver + state.update_tag_position(...)
