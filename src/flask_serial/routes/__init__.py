# flask_serial/routes/__init__.py
"""Blueprints HTTP de flask_serial.

Cada submódulo define un Blueprint llamado `bp`. Se registran en
`create_app()` con `app.register_blueprint(module.bp)`.
"""
from flask_serial.routes import commands, health, processing, stream

__all__ = ["health", "commands", "processing", "stream"]