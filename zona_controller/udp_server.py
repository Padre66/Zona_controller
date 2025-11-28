import socket
import threading
import time

from .config import ConfigManager
from .crypto import CryptoEngine
from .state import State
from .tdoa import TDoAProcessor
from .forward import PositionForwarder


class UDPServer(threading.Thread):
    def __init__(self, config_path: str, state: State):
        super().__init__(daemon=True)
        self.cfg_mgr = ConfigManager(config_path)
        cfg = self.cfg_mgr.get_config()
        net = cfg.get("network", {})
        host = net.get("udp_host", "0.0.0.0")
        port = int(net.get("udp_port", 512))

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))

        aes_key_hex = cfg.get("crypto", {}).get("aes_key_hex", "")
        if not aes_key_hex:
            raise ValueError("Missing crypto.aes_key_hex in config")
        aes_key = bytes.fromhex(aes_key_hex)
        self.crypto = CryptoEngine(aes_key, cfg)
        self.state = state
        self.tdoa = TDoAProcessor(state)
        self.forwarder = PositionForwarder(cfg)

    def run(self):
        print("[UDP] Listening on socket")
        while True:
            data, addr = self.sock.recvfrom(4096)
            ts = time.time()
            decoded, mode = self.crypto.try_decrypt_variants(data)
            self.state.update_last_message(addr, data, decoded, mode)

            if decoded:
                # Kalman szűrés + pozíció állapot
                self.tdoa.update_from_message(decoded, ts)
                parsed = self.tdoa.parse_message(decoded)
                if parsed:
                    tag_id, x, y, z = parsed
                    # forward eredmény a cél eszközre
                    self.forwarder.forward(tag_id, x, y, z, ts)
