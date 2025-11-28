from typing import Optional, Tuple

from Crypto.Cipher import AES
from Crypto.Util import Counter

PRINTABLE_PREFIXES = ("UWB:", "BLINK:", "TAG", "ver=", "HB", "HB:", "HB ")


def is_printable_ascii(b: bytes) -> bool:
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

    if s.startswith(PRINTABLE_PREFIXES):
        return True
    return False


class CryptoEngine:
    def __init__(self, aes_key: bytes, config: dict):
        self.aes_key = aes_key
        crypto_cfg = config.get("crypto", {})
        self.enable_gcm_first_nonce = crypto_cfg.get("enable_gcm_first_nonce", True)
        self.enable_gcm_zero_nonce = crypto_cfg.get("enable_gcm_zero_nonce", True)
        self.enable_ctr_first_iv = crypto_cfg.get("enable_ctr_first_iv", True)

    def try_decrypt_variants(self, data: bytes) -> Tuple[Optional[str], Optional[str]]:
        if len(data) <= 16:
            return None, None

        # 1) AES-GCM: nonce = első 12 byte, ct = közép, tag = utolsó 16 byte
        if self.enable_gcm_first_nonce and len(data) > 12 + 16:
            nonce = data[:12]
            tag = data[-16:]
            ct = data[12:-16]
            try:
                cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=nonce)
                pt = cipher.decrypt_and_verify(ct, tag)
                if looks_like_line(pt):
                    return pt.decode("ascii", errors="replace").strip(), "GCM[nonce=first12]"
            except Exception:
                pass

        # 2) AES-GCM: nonce = 12 x 0x00, ct = data[:-16], tag = data[-16:]
        if self.enable_gcm_zero_nonce and len(data) > 16:
            nonce = b"\x00" * 12
            tag = data[-16:]
            ct = data[:-16]
            try:
                cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=nonce)
                pt = cipher.decrypt_and_verify(ct, tag)
                if looks_like_line(pt):
                    return pt.decode("ascii", errors="replace").strip(), "GCM[nonce=0]"
            except Exception:
                pass

        # 3) AES-CTR: IV = első 16 byte, ciphertext = maradék
        if self.enable_ctr_first_iv and len(data) > 16:
            iv = data[:16]
            ct = data[16:]
            try:
                ctr = Counter.new(128, initial_value=int.from_bytes(iv, "big"))
                cipher = AES.new(self.aes_key, AES.MODE_CTR, counter=ctr)
                pt = cipher.decrypt(ct)
                if looks_like_line(pt):
                    return pt.decode("ascii", errors="replace").strip(), "CTR[iv=first16]"
            except Exception:
                pass

        return None, None
