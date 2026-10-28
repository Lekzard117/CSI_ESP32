from flask import Blueprint, jsonify, render_template

bp = Blueprint("main", __name__)  # sin url_prefix → responde en /


@bp.get("/")
def index():
    return jsonify({
        "servicio": "flask_serial",
        "status": "ok",
        "docs": "/api/health",
    })