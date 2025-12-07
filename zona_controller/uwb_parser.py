# zona_controller/uwb_parser.py

from typing import Optional, Dict, Any


def parse_uwb_header(line: str) -> Optional[Dict[str, Any]]:
    """
    Várható forma:
        UWB: ver=1 sync=60 tag_seq=12 batt=90% anchor=0x04000020 tag=0x02006655 ts=908823146933 zone_id=0x5A31
    """
    line = line.strip()
    if not line.startswith("UWB:"):
        return None

    payload = line[len("UWB:"):].strip()

    fields: Dict[str, Any] = {}
    tokens = payload.split()

    for tok in tokens:
        if "=" not in tok:
            continue
        key, value = tok.split("=", 1)
        key = key.strip()
        value = value.strip()

        # nyers stringben is eltesszük
        fields[key] = value

        if key in ("ver", "sync", "tag_seq"):
            try:
                fields[key] = int(value)
            except ValueError:
                pass
        elif key == "batt":
            if value.endswith("%"):
                try:
                    fields["batt_percent"] = int(value[:-1])
                except ValueError:
                    pass
        elif key == "anchor":
            fields["anchor_hex"] = value
            try:
                fields["anchor_id"] = int(value, 16)
            except ValueError:
                pass
        elif key == "tag":
            fields["tag_hex"] = value
            try:
                fields["tag_id"] = int(value, 16)
            except ValueError:
                pass
        elif key == "ts":
            try:
                fields["ts_raw"] = int(value)
            except ValueError:
                pass
        elif key == "zone_id":
            fields["zone_id_hex"] = value
            try:
                fields["zone_id"] = int(value, 16)
            except ValueError:
                pass

    return fields
