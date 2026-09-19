"""Endpoints de salud y diagnóstico."""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from flask_serial import state as state_module

bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/status")
def status():
    """Estado completo: readers, workers, ventanas."""
    s = state_module.app_state
    if s is None:
        return jsonify({"status": "no_state"}), 503
    return jsonify({
        "status": "ok",
        "servicio": "flask_serial",
        "state": s.status,
    })


@bp.get("/config")
def config():
    """Configuración no sensible (para debugging)."""
    return jsonify({
        "serial_ports": current_app.config.get("SERIAL_PORTS"),
        "serial_baud": current_app.config.get("SERIAL_BAUD"),
        "pipeline_window_size": current_app.config.get("PIPELINE_WINDOW_SIZE"),
        "pipeline_n_subcarriers": current_app.config.get("PIPELINE_N_SUBCARRIERS"),
        "pipeline_trim_guard": current_app.config.get("PIPELINE_TRIM_GUARD"),
    })


@bp.get("/health")
def health():
    """Liveness probe (sin dependencias)."""
    return jsonify({"status": "alive"})