"""Endpoints para enviar comandos al firmware ESP32."""
from __future__ import annotations

import time

from flask import Blueprint, jsonify, request

from flask_serial import state as state_module
from flask_serial.commands import send_reset, send_settime

bp = Blueprint("commands", __name__, url_prefix="/api/command")


def _get_reader(port: str):
    s = state_module.app_state
    if s is None:
        return None, (jsonify({"error": "app_state not initialized"}), 503)
    reader = s.get_reader(port)
    if reader is None:
        return None, (jsonify({"error": f"unknown port {port}"}), 404)
    if not reader.is_connected:
        return None, (jsonify({"error": f"port {port} not connected"}), 503)
    return reader, None


@bp.post("/settime")
def settime():
    payload = request.get_json(silent=True) or {}
    port = payload.get("port", "/dev/ttyUSB0")
    unix_seconds = payload.get("unix_seconds", int(time.time()))

    reader, err = _get_reader(port)
    if err:
        return err

    try:
        send_settime(reader, int(unix_seconds))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "status": "sent",
        "port": port,
        "unix_seconds": int(unix_seconds),
    })


@bp.post("/reset")
def reset():
    payload = request.get_json(silent=True) or {}
    port = payload.get("port", "/dev/ttyUSB0")

    reader, err = _get_reader(port)
    if err:
        return err

    try:
        send_reset(reader)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"status": "sent", "port": port})