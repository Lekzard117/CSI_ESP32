"""Entidad de dominio que representa un frame CSI ya convertido.

Un CsiLine crudo (lista de ints I/Q intercalados) se convierte en un
CsiFrame con un vector complejo de 64 subportadoras y su amplitud.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# El ESP32-CSI-Tool emite 64 subportadoras (HT20, 1 antena RX).
# Los primeros 6 y últimos 5 valores suelen ser ceros de guarda.
N_SUBCARRIERS = 64
GUARD_LOW = 6
GUARD_HIGH = 5


@dataclass
class CsiFrame:
    """Frame CSI normalizado, listo para el pipeline."""

    timestamp: float                    # real_timestamp o local_timestamp
    source_mac: Optional[str]           # MAC del emisor (None si nula)
    rssi: Optional[int]
    noise_floor: Optional[int]
    channel: Optional[int]
    local_timestamp: Optional[int]

    subcarriers: np.ndarray             # shape (64,), dtype complex64
    amplitudes: np.ndarray              # shape (64,), dtype float32

    # Métricas de calidad
    n_valid: int = 0                    # subportadoras no nulas
    is_valid: bool = False              # False si todo es cero

    @classmethod
    def from_csi_data(
        cls,
        csi_data: list[int],
        *,
        timestamp: float,
        source_mac: Optional[str] = None,
        rssi: Optional[int] = None,
        noise_floor: Optional[int] = None,
        channel: Optional[int] = None,
        local_timestamp: Optional[int] = None,
        trim_guard: bool = True,
    ) -> "CsiFrame":
        """Convierte la lista cruda [imag0, real0, imag1, real1, ...] a complejo.

        El firmware ESP32-CSI-Tool emite pares I/Q con el imaginario primero:
            [Q0, I0, Q1, I1, ..., Q63, I63]
        por lo que reconstruimos z = I + jQ tomando índices impares como real
        e índices pares como imaginario.

        Nota: algunos forks emiten [I0, Q0, ...]. Si los scores salen
        invertidos, cambiar `real = arr[0::2]`.
        """
        arr = np.asarray(csi_data, dtype=np.float32)

        # Truncar a longitud par (por seguridad si llega impar)
        if arr.size % 2 != 0:
            arr = arr[:-1]

        # Firmware ESP32-CSI-Tool: imaginario primero
        imag = arr[0::2]
        real = arr[1::2]

        z = (real + 1j * imag).astype(np.complex64)

        # Padding/truncado a N_SUBCARRIERS
        n = z.size
        if n < N_SUBCARRIERS:
            z = np.pad(z, (0, N_SUBCARRIERS - n), constant_values=0)
        elif n > N_SUBCARRIERS:
            z = z[:N_SUBCARRIERS]

        # Opcional: descartar subportadoras de guarda (ceros)
        if trim_guard:
            z = z[GUARD_LOW:N_SUBCARRIERS - GUARD_HIGH]

        # Detectar validez: al menos 1 subportadora no nula
        n_valid = int(np.count_nonzero(np.abs(z)))
        is_valid = n_valid > 0

        return cls(
            timestamp=timestamp,
            source_mac=source_mac,
            rssi=rssi,
            noise_floor=noise_floor,
            channel=channel,
            local_timestamp=local_timestamp,
            subcarriers=z,
            amplitudes=np.abs(z).astype(np.float32),
            n_valid=n_valid,
            is_valid=is_valid,
        )

    @property
    def shape(self) -> tuple[int, ...]:
        return self.subcarriers.shape