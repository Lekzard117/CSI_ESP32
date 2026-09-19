# - Abrir el puerto serial, leer bytes, ensamblar líneas y emitir CsiLine.
from __future__ import annotations

import logging
import os
import time
from typing import Generator, List, Optional

import serial
from serial.serialutil import SerialException

from flask_serial.models import CsiLine
from flask_serial.parser import parse_line

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
            self.last_rx = time.time()
            logger.info(f"Connected to {self.port} at {self.baud} baud")
            return True
        except SerialException:
            logger.exception(f"Failed to connect to {self.port}")
            self._ser = None
            return False

    def disconnect(self):
        if self._ser is not None:
            try:
                if self._ser.is_open:
                    self._ser.close()
                    logger.info(f"Disconnected from {self.port}")
            except SerialException:
                logger.exception(f"Error closing {self.port}")
        self._ser = None

    @property
    def is_connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    def reconnect(self):
        self.disconnect()
        time.sleep(RECONNECT_DELAY)
        self.connect()

    def _flush_lines(self) -> Generator[CsiLine, None, None]:
        while b"\n" in self._buffer:
            raw_bytes, self._buffer = self._buffer.split(b"\n", 1)
            raw_str = raw_bytes.decode("utf-8", errors="replace").strip()
            if not raw_str:
                continue
            try:
                line = parse_line(raw_str)
                self.line_count += 1
                yield line
            except ValueError as e:
                self.error_count += 1
                logger.warning(f"Parse error on {self.port}: {e}")

    def lines(self) -> Generator[CsiLine, None, None]:
        if not self.is_connected:
            raise RuntimeError("Not connected. Call connect() first")
        while True:
            if not self.is_connected:
                time.sleep(RECONNECT_DELAY)
                self.connect()
                continue
            try:
                data = self._ser.read(4096)
                if data:
                    self.last_rx = time.time()
                    self._buffer.extend(data)
                    yield from self._flush_lines()
                else:
                    if time.time() - self.last_rx > TIMEOUT_SECONDS:
                        logger.warning(f"Timeout on {self.port}")
                        self.reconnect()
            except SerialException as e:
                logger.error(f"Serial error on {self.port}: {e}")
                self.reconnect()


#def create_readers() -> List[SerialReader]:
    #ports_str = os.getenv("SERIAL_PORTS", "/dev/ttyUSB0")
    #readers: List[SerialReader] = []
    #for port in ports_str.split(","):
        #port = port.strip()
        #if port:
            #readers.append(SerialReader(port, baud=921600))
    #return readers
def create_readers() -> List[SerialReader]:
    ports_str = os.getenv("SERIAL_PORTS", "/dev/ttyUSB0")
    baud = int(os.getenv("SERIAL_BAUD", "115200"))  # ⚠️
    readers = []
    for port in ports_str.split(","):
        port = port.strip()
        if port:
            readers.append(SerialReader(port, baud=baud))
    return readers
 