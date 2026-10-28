# -- Convertir una línea CSV cruda del ESP32 en un objeto CsiLine.
from __future__ import annotations

import re
from typing import List, Optional

from flask_serial.models import CsiLine, Role

# Parser tolerante con regex: tolera espacios, tabs, comas, tokens corruptos.
# Nota: si en el futuro se sube el baud a 921600, esta tolerancia sigue siendo
# útil porque el framing serial puede seguir partiendo números.

_NUMBER_RE = re.compile(r"-?\d+")
_BRACKET_RE = re.compile(r"\[([^\]]*)\]")


def parse_line(raw: str) -> CsiLine:
    raw = raw.strip()
    if not raw:
        raise ValueError("empty line")

    # Estrategia: localizar el bracket CSI directamente
    bracket_match = _BRACKET_RE.search(raw)
    if not bracket_match:
        raise ValueError(f"no CSI bracket found: {raw[:40]}")

    csi_raw = bracket_match.group(0)
    csi_values = _parse_csi_bracket(csi_raw)

    # Los metadatos están ANTES del bracket
    meta_raw = raw[:bracket_match.start()].rstrip(",")
    parts = meta_raw.split(",") if meta_raw else []

    if not parts or parts[0] != "CSI_DATA":
        raise ValueError(f"invalid prefix: {parts[0][:20] if parts else 'EMPTY'}")

    # Rellenar hasta 25 campos
    while len(parts) < 25:
        parts.append("")

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
    """Extrae TODOS los enteros del interior del bracket.

    Tolerante a:
      '-3-31'  → [-3, -31]   (token partido por framing serial)
      '   '    → []
      '[1 2]'  → [1, 2]
    """
    raw = raw.strip()
    if not raw.startswith("[") or not raw.endswith("]"):
        raise ValueError(f"not bracket-delimited: {raw[:20]}")
    inner = raw[1:-1]
    return [int(v) for v in _NUMBER_RE.findall(inner)]


def _int(v: str) -> Optional[int]:
    if not v:
        return None
    m = _NUMBER_RE.fullmatch(v.strip())
    return int(m.group()) if m else None


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