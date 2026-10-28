from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

"""
rssi	Diagnóstico	✅ Sí, filtrar
noise_floor	Diagnóstico	⚠️ Puede omitirse
rate, mcs, bandwidth, sig_mode, rx_state, ant, type	Constantes	✅ Sí, descartar
smoothing, not_sounding, aggregation, stbc, fec_coding, sgi	Constantes	✅ Sí, descartar
ampdu_cnt, secondary_channel	Diagnóstico	✅ Sí, descartar"""

class Role(Enum):
    AP = "AP"
    PASSIVE = "PASSIVE"
    STA = "STA"

@dataclass
class CsiLine:
    # --- Identidad / enrutamiento ---
    type: str = "CSI_DATA"
    role: Optional[Role] = None
    mac: Optional[str] = None

    # --- Calidad de canal ---
    rssi: Optional[int] = None
    noise_floor: Optional[int] = None 
    # --- Sincronización ---
    channel: Optional[int] = None
    local_timestamp: Optional[int] = None
    real_timestamp: Optional[float] = None
    real_time_set: Optional[bool] = None

    # --- Longitud / estructura ---
    sig_len: Optional[int] = None
    len: Optional[int] = None

    # --- Calibración hardware (críticos para AGC) ---
    agc_gain: Optional[float] = None      # ← NUEVO
    fft_gain: Optional[float] = None      # ← NUEVO

    # --- Datos primarios ---
    csi_data: List[int] = field(default_factory=list)
# agc_gain en tus logs aparece como 50, 78, 79. Puede ser int o float; usar Optional[float] es más flexible.