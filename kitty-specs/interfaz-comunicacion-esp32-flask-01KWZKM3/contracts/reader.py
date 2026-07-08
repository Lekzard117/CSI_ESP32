import os
import time
import logging
from typing import List, Optional, Generator

import serial

from flask_serial.parser import parse_line
from flask_serial.models import CsiLine

logger = logging.getLogger(__name__)

RECONNECT_DELAY = 2
TIMEOUT_SECONDS = 5


class SerialReader:
    def __init__(self, port: str, baud: int = 921600):
        self.port = port
        self.baud = baud
        self._ser: Optional[serial.Serial] = None
        self._buffer = bytearray()
        self.line_count = 0
        self.error_count = 0
        self.last_rx = 0.0

    def connect(self) -> bool:
        try:
            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baud,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
            logger.info(f"Connected to {self.port} at {self.baud} baud")
            return True
        except serial.SerialException as e:
            logger.error(f"Failed to connect to {self.port}: {e}")
            return False

    def disconnect(self):
        if self._ser and self._ser.is_open:
            self._ser.close()
            logger.info(f"Disconnected from {self.port}")

    def reconnect(self):
        self.disconnect()
        time.sleep(RECONNECT_DELAY)
        self.connect()

    def lines(self) -> Generator[CsiLine, None, None]:
        if not self._ser or not self._ser.is_open:
            raise RuntimeError("Not connected. Call connect() first")

        while True:
            try:
                data = self._ser.read(4096)
                if data:
                    self.last_rx = time.time()
                    self._buffer.extend(data)
                    yield from self._flush_lines()
                else:
                    if time.time() - self.last_rx > TIMEOUT_SECONDS:
                        logger.warning(f"Timeout on {self.port}, reconnecting...")
                        self.reconnect()
            except serial.SerialException:
                logger.error(f"Serial error on {self.port}")
                self.reconnect()

    def _flush_lines(self) -> Generator[CsiLine, None, None]:
        while b"\n" in self._buffer:
            raw, self._buffer = self._buffer.split(b"\n", 1)
            raw_str = raw.decode("utf-8", errors="replace").strip()
            if not raw_str:
                continue
            try:
                line = parse_line(raw_str)
                self.line_count += 1
                yield line
            except ValueError as e:
                self.error_count += 1
                logger.warning(f"Parse error: {e}")


def create_readers() -> List[SerialReader]:
    ports_str = os.getenv("SERIAL_PORTS", "/dev/ttyUSB0")
    readers = []
    for port in ports_str.split(","):
        port = port.strip()
        if port:
            readers.append(SerialReader(port))
    return readers
