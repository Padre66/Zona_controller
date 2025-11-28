from typing import Dict, Tuple, Optional

from .state import State


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
    def __init__(self, state: State):
        self.state = state
        self.filters: Dict[str, KalmanFilter2D] = {}

    def parse_message(self, decoded: str) -> Optional[Tuple[str, float, float, float]]:
        try:
            parts = decoded.split(",")
            kv = {}
            for p in parts:
                if ":" in p:
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

    def update_from_message(self, decoded: str, ts: float):
        parsed = self.parse_message(decoded)
        if not parsed:
            return
        tag_id, x_meas, y_meas, z_meas = parsed

        # Kalman szűrő TAG-enként
        kf = self.filters.get(tag_id)
        if kf is None:
            kf = KalmanFilter2D(x_meas, y_meas)
            self.filters[tag_id] = kf
        kf.step(ts, (x_meas, y_meas))
        x_f, y_f, vx_f, vy_f = kf.get_state()

        self.state.update_tag_position(tag_id, x_f, y_f, z_meas, ts)
