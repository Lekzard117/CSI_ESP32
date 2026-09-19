"""Streaming SSE de líneas CSI en vivo."""
from __future__ import annotations

import json

from flask import Blueprint, Response, jsonify, request, stream_with_context

from flask_serial import state as state_module

bp = Blueprint("stream", __name__, url_prefix="/api")


@bp.get("/stream")
def stream():
    """Server-Sent Events: una línea CSI por evento."""
    port = request.args.get("port", "/dev/ttyUSB0")
    limit = request.args.get("limit", type=int)

    s = state_module.app_state
    if s is None:
        return jsonify({"error": "app_state not initialized"}), 503

    window = s.get_window(port)
    if window is None:
        return jsonify({"error": f"unknown port {port}"}), 404

    # TODO Fase 1: suscribirse al Broadcaster en lugar de snapshot
    def generate():
        yield ": connected\n\n"
        # Placeholder: en Fase 1 se conecta al Broadcaster
        yield f"data: {json.dumps({'status': 'not_implemented'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@bp.get("/read")
def read_once():
    """Lee la última ventana como JSON (polling simple)."""
    port = request.args.get("port", "/dev/ttyUSB0")
    s = state_module.app_state
    if s is None:
        return jsonify({"error": "app_state not initialized"}), 503

    window = s.get_window(port)
    if window is None:
        return jsonify({"error": f"unknown port {port}"}), 404

    snap = window.snapshot()
    if snap is None:
        return jsonify({"error": "no data yet"}), 404

    return jsonify({
        "port": port,
        "shape": list(snap.shape),
        "amplitudes": snap.amplitudes.tolist(),
        "rssi": snap.rssi.tolist(),
    })