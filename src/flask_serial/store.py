"""Repositorio de ventanas CSI. MVP: solo la última en memoria."""
from __future__ import annotations

import threading
from typing import Dict, Optional

from flask_serial.csi_window import CsiWindow


class WindowStore:
    """Una CsiWindow por puerto serial (multi-ESP32 ready)."""

    def __init__(self, window_size: int = 100, n_subcarriers: int = 53):
        self.window_size = window_size
        self.n_subcarriers = n_subcarriers
        self._windows: Dict[str, CsiWindow] = {}
        self._lock = threading.Lock()

    def get_or_create(self, port: str) -> CsiWindow:
        with self._lock:
            if port not in self._windows:
                self._windows[port] = CsiWindow(
                    size=self.window_size,
                    n_subcarriers=self.n_subcarriers,
                )
            return self._windows[port]

    def get(self, port: str) -> Optional[CsiWindow]:
        with self._lock:
            return self._windows.get(port)

    @property
    def ports(self) -> list[str]:
        with self._lock:
            return list(self._windows.keys())

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                port: w.stats for port, w in self._windows.items()
            }