#!/usr/bin/env python3
import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from Crypto.Cipher import AES
from Crypto.Util import Counter

HTTP_PORT = 51200
UDP_PORT = 512

AES_KEY_HEX = "00112233445566778899AABBCCDDEEFF"
AES_KEY = bytes.fromhex(AES_KEY_HEX)

# közös állapot
last_msg = {
    "time": None,
    "from": None,
    "raw_len": 0,
    "raw_hex": "",
    "decoded": None,     # a teljes dekódolt sor (string)
    "mode": None         # melyik próbálkozás működött
}
last_lock = threading.Lock()


def is_printable_ascii(b: bytes) -> bool:
    # engedjük a CR/LF/TAB-et is
    for x in b:
        if x in (9, 10, 13):
            continue
        if x < 32 or x > 126:
            return False
    return True


def looks_like_line(pt: bytes) -> bool:
    if not pt:
        return False
    if not is_printable_ascii(pt):
        return False

    s = pt.decode("ascii", errors="replace").strip()
    if not s:
        return False

    # új prefixek engedése
    if s.startswith(("UWB:", "BLINK:", "TAG", "ver=", "HB", "HB:", "HB ")):
        return True

    return False


def try_decrypt_variants(data: bytes):
    """
    Több variáns kipróbálása.
    Visszatér: (plaintext_str, mode) vagy (None, None)
    mode: szöveges jelölés, hogy melyik ágon sikerült.
    """

    # 0) ha rövidebb, mint 16 byte, biztos nem az
    if len(data) <= 16:
        return None, None

    # 1) AES-GCM: nonce = első 12 byte, ct = közép, tag = utolsó 16 byte
    if len(data) > 12 + 16:
        nonce = data[:12]
        tag = data[-16:]
        ct = data[12:-16]
        try:
            cipher = AES.new(AES_KEY, AES.MODE_GCM, nonce=nonce)
            pt = cipher.decrypt_and_verify(ct, tag)
            if looks_like_line(pt):
                return pt.decode("ascii", errors="replace").strip(), "GCM[nonce=first12]"
        except Exception:
            pass

    # 2) AES-GCM: nonce = 12 x 0x00, ct = data[:-16], tag = data[-16:]
    if len(data) > 16:
        nonce = b"\x00" * 12
        tag = data[-16:]
        ct = data[:-16]
        try:
            cipher = AES.new(AES_KEY, AES.MODE_GCM, nonce=nonce)
            pt = cipher.decrypt_and_verify(ct, tag)
            if looks_like_line(pt):
                return pt.decode("ascii", errors="replace").strip(), "GCM[nonce=0]"
        except Exception:
            pass

    # 3) AES-CTR: IV = első 16 byte, ciphertext = maradék
    if len(data) > 16:
        iv = data[:16]
        ct = data[16:]
        try:
            ctr = Counter.new(128, initial_value=int.from_bytes(iv, "big"))
            cipher = AES.new(AES_KEY, AES.MODE_CTR, counter=ctr)
            pt = cipher.decrypt(ct)
            if looks_like_line(pt):
                return pt.decode("ascii", errors="replace").strip(), "CTR[iv=first16]"
        except Exception:
            pass

    # ha egyik sem adott értelmes sort
    return None, None


# ---------------- HTTP -------------------

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # ne spam-eljen
        return

    def do_GET(self):
        if self.path == "/api/status":
            with last_lock:
                resp = {
                    "status": "ok",
                    "last_msg": last_msg
                }
            data = json.dumps(resp, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()


def run_http_server():
    server_address = ("0.0.0.0", HTTP_PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"[HTTP] szerver elindult a {HTTP_PORT}-as porton (GET /api/status)")
    httpd.serve_forever()


# ---------------- UDP FOGADÓ -------------------

def run_udp_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    print(f"[UDP] fogadó elindult: 0.0.0.0:{UDP_PORT}")

    while True:
        data, addr = sock.recvfrom(4096)
        ts = time.time()

        #print("\n--- UDP csomag érkezett ---")
        #print(f"   From : {addr[0]}:{addr[1]}")
        #print(f"   Len  : {len(data)} byte")
        #print(f"   Hex  : {data.hex()}")

        decoded, mode = try_decrypt_variants(data)
        #if decoded is not None:
            # print(f"   DECODED ({mode}): {decoded}")
            # print(f"{decoded}")
        #else:
        #    print("   DECODED : [nem sikerült értelmesen dekódolni]")

        with last_lock:
            last_msg["time"] = ts
            last_msg["from"] = f"{addr[0]}:{addr[1]}"
            last_msg["raw_len"] = len(data)
            last_msg["raw_hex"] = data.hex()
            last_msg["decoded"] = decoded
            last_msg["mode"] = mode


# ---------------- main -------------------

if __name__ == "__main__":
    t_http = threading.Thread(target=run_http_server, daemon=True)
    t_http.start()
    run_udp_receiver()
