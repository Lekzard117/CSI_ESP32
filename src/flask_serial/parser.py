from typing import List, Optional

from flask_serial.models import CsiLine, Role


def parse_line(raw: str) -> CsiLine:
    parts = raw.strip().split(",")

    if len(parts) < 26:
        raise ValueError(f"Expected >=26 fields (25 metadata + CSI_DATA), got {len(parts)}")

    if parts[0] != "CSI_DATA":
        raise ValueError(f"Invalid prefix: {parts[0]}")

    csi_raw = parts[25]
    csi_values = _parse_csi_bracket(csi_raw)

    line = CsiLine(
        type=parts[0],
        role=Role(parts[1]) if parts[1] in {"AP", "PASSIVE", "STA"} else None,
        mac=parts[2] if parts[2] else None,
        rssi=_int(parts[3]),
        rate=_int(parts[4]),
        sig_mode=_int(parts[5]),
        mcs=_int(parts[6]),
        bandwidth=_int(parts[7]),
        smoothing=_bool(parts[8]),
        not_sounding=_bool(parts[9]),
        aggregation=_bool(parts[10]),
        stbc=_bool(parts[11]),
        fec_coding=_bool(parts[12]),
        sgi=_bool(parts[13]),
        noise_floor=_int(parts[14]),
        ampdu_cnt=_int(parts[15]),
        channel=_int(parts[16]),
        secondary_channel=_int(parts[17]),
        local_timestamp=_int(parts[18]),
        ant=_int(parts[19]),
        sig_len=_int(parts[20]),
        rx_state=_int(parts[21]),
        real_time_set=_bool(parts[22]),
        real_timestamp=_float(parts[23]),
        len=_int(parts[24]),
        csi_data=csi_values,
    )

    return line


def _parse_csi_bracket(raw: str) -> List[int]:
    raw = raw.strip()
    if not raw.startswith("[") or not raw.endswith("]"):
        raise ValueError(f"CSI_DATA must be bracket-delimited [...], got: {raw[:20]}")
    inner = raw[1:-1].strip()
    if not inner:
        return []
    return [int(v) for v in inner.split()]


def _int(v: str) -> Optional[int]:
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def _float(v: str) -> Optional[float]:
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def _bool(v: str) -> Optional[bool]:
    try:
        return bool(int(v))
    except (ValueError, TypeError):
        return None
