import socket
import threading
import time

from .config import ConfigManager
from .crypto import CryptoEngine
from .state import State
from .tdoa import TDoAProcessor
from .forward import PositionForwarder
from .runtime_params import TDoARuntimeParams


def _extract_zone_id_hex(decoded: str) -> str | None:
    # pl.: "... zone_id=0x5A31"
    for tok in decoded.split():
        if tok.startswith("zone_id="):
            return tok.split("=", 1)[1].strip()
    return None


class UDPServer(threading.Thread):
    def __init__(self, config_path: str, state: State,
                 processor: TDoAProcessor, params: TDoARuntimeParams):
        super().__init__(daemon=True)

        self.cfg_mgr = ConfigManager(config_path)
        cfg = self.cfg_mgr.get_config()

        net = cfg.get("network", {})
        host = net.get("udp_host", "0.0.0.0")
        port = int(net.get("udp_port", 100))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))

        aes_key_hex = cfg.get("crypto", {}).get("aes_key_hex", "")
        if not aes_key_hex:
            raise ValueError("Missing crypto.aes_key_hex in config")
        aes_key = bytes.fromhex(aes_key_hex)

        self.crypto = CryptoEngine(aes_key, cfg)
        self.state = state
        self.processor = processor
        self.params = params
        self.forwarder = PositionForwarder(cfg)

    def run(self):
        print("[UDP] Listening on socket")
        while True:
            data, addr = self.sock.recvfrom(4096)
            ts = time.time()

            decoded, mode = self.crypto.try_decrypt_variants(data)

            # ELŐSZŰRÉS zóna alapján: ami itt nem megy át, az sehová nem kerül
            if decoded:
                zone_cfg = self.params.get_zone_params()
                expected_hex = zone_cfg.get("expected_zone_id_hex")
                if expected_hex:
                    zone_hex = _extract_zone_id_hex(decoded)
                    # ha nincs zone_id, vagy nem egyezik → eldobjuk a csomagot
                    if zone_hex != expected_hex:
                        continue

            # CSAK az engedélyezett csomagok frissítik az állapotot
            self.state.update_last_message(addr, data, decoded, mode)

            if decoded:
                self.processor.update_from_message(decoded, ts)
