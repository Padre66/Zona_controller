import socket
from typing import Dict


class PositionForwarder:
    """
    Egyszerű UDP forward: TAG pozíciók továbbítása cél host:port-ra.
    """
    def __init__(self, cfg: Dict):
        net = cfg.get("network", {})
        sink_host = net.get("sink_host", None)
        sink_port = net.get("sink_port", None)
        self.enabled = sink_host is not None and sink_port is not None
        self.host = sink_host
        self.port = int(sink_port) if sink_port is not None else None

    def forward(self, tag_id: str, x: float, y: float, z: float, ts: float):
        if not self.enabled:
            return
        msg = f"TAG:{tag_id},X:{x:.3f},Y:{y:.3f},Z:{z:.3f},T:{ts:.3f}"
        data = msg.encode("ascii")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.sendto(data, (self.host, self.port))
        finally:
            sock.close()
