"""Hilo daemon que consume SerialReader y alimenta CsiWindow.

Este es el pegamento que faltaba entre Capa 1 (adquisición) y
Capa 2 (procesamiento).
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from flask_serial.csi_frame import CsiFrame
from flask_serial.csi_window import CsiWindow
from flask_serial.reader import SerialReader

logger = logging.getLogger(__name__)

# Si no llegan datos en este tiempo, avisamos (pero no matamos el hilo)
STALL_WARNING_SECONDS = 10.0


class AcquisitionWorker:
    """Consume lines() de un SerialReader y publica CsiFrame en una CsiWindow."""

    def __init__(
        self,
        reader: SerialReader,
        window: CsiWindow,
        *,
        trim_guard: bool = True,
        skip_null_mac: bool = False,
    ):
        self.reader = reader
        self.window = window
        self.trim_guard = trim_guard
        self.skip_null_mac = skip_null_mac

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_frame_ts: float = 0.0
        self._frames_ingested: int = 0
        self._frames_dropped: int = 0

    # ------------------------------------------------------------------ #
    # Ciclo de vida
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name=f"AcquisitionWorker[{self.reader.port}]",
            daemon=True,
        )
        self._thread.start()
        logger.info("AcquisitionWorker started for %s", self.reader.port)

    def stop(self, timeout: float = 3.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        logger.info("AcquisitionWorker stopped for %s", self.reader.port)

    # ------------------------------------------------------------------ #
    # Loop principal
    # ------------------------------------------------------------------ #
    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                if not self.reader.is_connected:
                    if not self.reader.connect():
                        time.sleep(2.0)
                        continue

                self._consume_stream()
            except Exception:
                logger.exception("AcquisitionWorker crashed; restarting in 2s")
                time.sleep(2.0)

    def _consume_stream(self) -> None:
        for line in self.reader.lines():
            if self._stop_event.is_set():
                return

            frame = self._line_to_frame(line)
            if frame is None:
                self._frames_dropped += 1
                continue

            accepted = self.window.append(frame)
            self._last_frame_ts = time.time()

            if accepted:
                self._frames_ingested += 1
            else:
                self._frames_dropped += 1

            # Aviso si el stream se estanca
            if (time.time() - self._last_frame_ts) > STALL_WARNING_SECONDS:
                logger.warning("No CSI frames in %.1fs on %s",
                               STALL_WARNING_SECONDS, self.reader.port)

    # ------------------------------------------------------------------ #
    # Conversión
    # ------------------------------------------------------------------ #
    def _line_to_frame(self, line) -> Optional[CsiFrame]:
        if not line.csi_data:
            return None

        mac = line.mac
        if self.skip_null_mac and (not mac or mac == "00:00:00:00:00:00"):
            return None

        timestamp = line.real_timestamp or (
            line.local_timestamp / 1_000_000.0 if line.local_timestamp else 0.0
        )

        try:
            return CsiFrame.from_csi_data(
                line.csi_data,
                timestamp=float(timestamp),
                source_mac=mac,
                rssi=line.rssi,
                noise_floor=line.noise_floor,
                channel=line.channel,
                local_timestamp=line.local_timestamp,
                trim_guard=self.trim_guard,
            )
        except Exception:
            logger.exception("Failed to build CsiFrame")
            return None

    # ------------------------------------------------------------------ #
    # Métricas
    # ------------------------------------------------------------------ #
    @property
    def stats(self) -> dict:
        return {
            "port": self.reader.port,
            "alive": self._thread.is_alive() if self._thread else False,
            "frames_ingested": self._frames_ingested,
            "frames_dropped": self._frames_dropped,
            "last_frame_age_s": (
                time.time() - self._last_frame_ts if self._last_frame_ts else None
            ),
        }