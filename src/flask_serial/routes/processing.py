"""Endpoints de procesamiento: ventana CSI + pipeline de motion."""
from __future__ import annotations

from functools import partial

import numpy as np
from flask import Blueprint, jsonify, request

from flask_serial import state as state_module

bp = Blueprint("processing", __name__, url_prefix="/api")


def _get_state():
    return state_module.app_state


@bp.get("/windows")
def list_windows():
    """Lista puertos y estado de sus ventanas."""
    s = _get_state()
    if s is None:
        return jsonify({"error": "app_state not initialized"}), 503
    return jsonify({
        "ports": s.store.ports,
        "windows": s.store.stats,
    })


@bp.get("/latest")
def latest():
    """Última ventana lista para pipeline."""
    port = request.args.get("port", "/dev/ttyUSB0")
    s = _get_state()
    if s is None:
        return jsonify({"error": "app_state not initialized"}), 503

    window = s.get_window(port)
    if window is None:
        return jsonify({"error": f"unknown port {port}"}), 404

    if not window.is_ready():
        return jsonify({
            "status": "warming_up",
            "buffered": len(window),
            "required": window.size,
        }), 202

    snap = window.snapshot()
    return jsonify({
        "port": port,
        "shape": list(snap.shape),
        "timestamps": snap.timestamps.tolist(),
        "rssi": snap.rssi.tolist(),
        "macs": snap.macs,
        "amplitudes": snap.amplitudes.tolist(),
    })


@bp.post("/process")
def process():
    """Corre el pipeline sobre la ventana actual."""
    port = request.args.get("port", "/dev/ttyUSB0")
    s = _get_state()
    if s is None:
        return jsonify({"error": "app_state not initialized"}), 503

    window = s.get_window(port)
    if window is None:
        return jsonify({"error": f"unknown port {port}"}), 404
    if not window.is_ready():
        return jsonify({"error": "window not ready",
                        "buffered": len(window),
                        "required": window.size}), 409

    # Import lazy: scipy solo se carga cuando se usa el pipeline
    from flask_serial.pipeline import (
        Pipeline, agc_compensation, hampel_filter,
        savgol_filter, temporal_variance,
    )

    snap = window.snapshot()
    pipeline = Pipeline(stages=[
        ("agc", agc_compensation),
        ("hampel", partial(hampel_filter, k=3, nsigma=3)),
        ("savgol", partial(savgol_filter, window_length=15, polyorder=3)),
        ("variance", partial(temporal_variance, frame_size=5)),
    ])

    try:
        scores = pipeline.run(snap.amplitudes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    scores_json = np.where(np.isnan(scores), None, scores).tolist()
    return jsonify({
        "stages": pipeline.stage_names,
        "shape": list(snap.shape),
        "motion_scores": scores_json,
    })