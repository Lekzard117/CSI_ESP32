"""Ventana deslizante de CsiFrame, lista para el pipeline.

Mantiene una matriz (n_frames, n_subcarriers) compleja y amplitudes
equivalentes. La ventana se arma por conteo de frames válidos, NO por
tiempo: tolera pérdida de paquetes sin romper el pipeline.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Deque, List, Optional

import numpy as np

from flask_serial.csi_frame import CsiFrame


class CsiWindow:
    """Buffer circular thread-safe de CsiFrame."""

    def __init__(self, size: int = 100, n_subcarriers: int = 53):
        self.size = int(size)
        self.n_subcarriers = int(n_subcarriers)
        self._frames: Deque[CsiFrame] = deque(maxlen=self.size)
        self._lock = threading.Lock()
        self._total_seen = 0
        self._total_accepted = 0
        self._total_rejected = 0

    # ------------------------------------------------------------------ #
    # Escritura (desde AcquisitionWorker)
    # ------------------------------------------------------------------ #
    def append(self, frame: CsiFrame) -> bool:
        """Añade un frame si es válido. Devuelve True si se aceptó."""
        with self._lock:
            self._total_seen += 1
            if not frame.is_valid:
                self._total_rejected += 1
                return False
            self._frames.append(frame)
            self._total_accepted += 1
            return True

    # ------------------------------------------------------------------ #
    # Lectura (desde routes / pipeline)
    # ------------------------------------------------------------------ #
    def snapshot(self) -> Optional["CsiWindowSnapshot"]:
        """Copia consistente de la ventana actual."""
        with self._lock:
            if len(self._frames) < self.size:
                # Ventana incompleta: aún no lista para pipeline
                # (pero devolvemos lo que hay para diagnóstico)
                pass
            frames = list(self._frames)

        if not frames:
            return None

        return CsiWindowSnapshot.from_frames(frames, self.n_subcarriers)

    def is_ready(self) -> bool:
        """True cuando hay suficientes frames para correr el pipeline."""
        with self._lock:
            return len(self._frames) >= self.size

    def __len__(self) -> int:
        with self._lock:
            return len(self._frames)

    # ------------------------------------------------------------------ #
    # Métricas
    # ------------------------------------------------------------------ #
    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "size": self.size,
                "buffered": len(self._frames),
                "ready": len(self._frames) >= self.size,
                "total_seen": self._total_seen,
                "total_accepted": self._total_accepted,
                "total_rejected": self._total_rejected,
                "rejection_rate": (
                    self._total_rejected / self._total_seen
                    if self._total_seen else 0.0
                ),
            }


class CsiWindowSnapshot:
    """Vista inmutable de la ventana, segura para pasar al pipeline."""

    def __init__(
        self,
        subcarriers: np.ndarray,
        amplitudes: np.ndarray,
        timestamps: np.ndarray,
        macs: List[Optional[str]],
        rssi: np.ndarray,
    ):
        self.subcarriers = subcarriers      # (n_frames, n_sub)
        self.amplitudes = amplitudes        # (n_frames, n_sub)
        self.timestamps = timestamps        # (n_frames,)
        self.macs = macs                    # list[str | None]
        self.rssi = rssi                    # (n_frames,)

    @classmethod
    def from_frames(cls, frames: List[CsiFrame], n_sub: int) -> "CsiWindowSnapshot":
        n = len(frames)
        sub = np.zeros((n, n_sub), dtype=np.complex64)
        amp = np.zeros((n, n_sub), dtype=np.float32)
        ts = np.zeros(n, dtype=np.float64)
        rssi = np.zeros(n, dtype=np.float32)
        macs: List[Optional[str]] = []

        for i, f in enumerate(frames):
            k = min(f.subcarriers.size, n_sub)
            sub[i, :k] = f.subcarriers[:k]
            amp[i, :k] = f.amplitudes[:k]
            ts[i] = f.timestamp
            rssi[i] = f.rssi if f.rssi is not None else np.nan
            macs.append(f.source_mac)

        return cls(sub, amp, ts, macs, rssi)

    @property
    def shape(self) -> tuple[int, int]:
        return self.subcarriers.shape