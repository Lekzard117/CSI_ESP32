from __future__ import annotations

import logging
from typing import Dict, Optional

from flask_serial.acquisition import AcquisitionWorker
from flask_serial.reader import SerialReader, create_readers
from flask_serial.store import WindowStore

logger = logging.getLogger(__name__)


class AppState:
    def __init__(self, window_size: int = 100, n_subcarriers: int = 53):
        self.readers: Dict[str, SerialReader] = {}
        self.workers: Dict[str, AcquisitionWorker] = {}
        self.store = WindowStore(window_size=window_size, n_subcarriers=n_subcarriers)
        self._started = False

    def start(self) -> None:
        if self._started:
            return
        for reader in create_readers():
            if not reader.connect():
                logger.warning("Could not open %s", reader.port)
                continue

            window = self.store.get_or_create(reader.port)
            worker = AcquisitionWorker(reader, window)
            worker.start()

            self.readers[reader.port] = reader
            self.workers[reader.port] = worker

        self._started = True
        logger.info("AppState started with %d reader(s)", len(self.readers))

    def stop(self) -> None:
        for worker in self.workers.values():
            worker.stop()
        for reader in self.readers.values():
            reader.disconnect()
        self.workers.clear()
        self.readers.clear()
        self._started = False

    def get_reader(self, port: str) -> Optional[SerialReader]:
        return self.readers.get(port)

    def get_worker(self, port: str) -> Optional[AcquisitionWorker]:
        return self.workers.get(port)

    def get_window(self, port: str):
        return self.store.get(port)

    @property
    def status(self) -> dict:
        return {
            "started": self._started,
            "readers": {
                port: {
                    "connected": r.is_connected,
                    "lines": r.line_count,
                    "errors": r.error_count,
                }
                for port, r in self.readers.items()
            },
            "workers": {
                port: w.stats for port, w in self.workers.items()
            },
            "windows": self.store.stats,
        }


# Singleton — configurado en create_app
app_state: AppState | None = None