from __future__ import annotations

import logging

from serial.serialutil import SerialException

from flask_serial.reader import SerialReader

logger = logging.getLogger(__name__)


def send_settime(reader: SerialReader, unix_seconds: int) -> None:
    if not reader.is_connected:
        raise RuntimeError("Reader not connected")
    cmd = f"SETTIME:{unix_seconds}\n"
    try:
        reader._ser.write(cmd.encode("utf-8"))
        logger.info(f"SETTIME sent: {unix_seconds}")
    except SerialException:
        logger.exception("SETTIME failed")
        raise


def send_reset(reader: SerialReader) -> None:
    if not reader.is_connected:
        raise RuntimeError("Reader not connected")
    cmd = "RESET\n"
    try:
        reader._ser.write(cmd.encode("utf-8"))
        logger.info("RESET sent")
    except SerialException:
        logger.exception("RESET failed")
        raise
