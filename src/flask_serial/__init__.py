from __future__ import annotations 
#Permite usar sintaxis moderna de tipos (como dict | None) 
# incluso en versiones de Python donde aún no sería válido evaluarlas en tiempo de ejecución. 
# Las anotaciones se tratan como strings.

from flask import Flask
#patron aplication factory de flask
import atexit
import logging
import os

from flask_serial.models import CsiLine, Role
from flask_serial.parser import parse_line
from flask_serial.reader import SerialReader, create_readers
from flask_serial.routes.commands import send_settime, send_reset

from flask_serial import state as state_module

logger = logging.getLogger(__name__)

def create_app(config: dict | None = None) -> Flask:
    """Application factory."""
    """Recibe opcionalmente un diccionario de configuración y devuelve una instancia de Flask ya configurada."""
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev-key-change-me",
        SERIAL_PORTS="/dev/ttyUSB0",
        SERIAL_BAUD=int(os.getenv("SERIAL_BAUD", "115200")),  # ⚠️ 115200, no 921600
        PIPELINE_WINDOW_SIZE=int(os.getenv("PIPELINE_WINDOW_SIZE", "100")),
        #PIPELINE_KEEP_SUBCARRIERS=int(os.getenv("PIPELINE_KEEP_SUBCARRIERS", "2")),
        PIPELINE_N_SUBCARRIERS=int(os.getenv("PIPELINE_N_SUBCARRIERS", "53")),
        PIPELINE_TRIM_GUARD=os.getenv("PIPELINE_TRIM_GUARD", "1") == "1",

    )
    if config:
        app.config.update(config)

    # Registrar blueprints / rutas
    from flask_serial.routes import health, commands, processing, stream
  
    app.register_blueprint(commands.bp)
    app.register_blueprint(processing.bp)
    app.register_blueprint(stream.bp)

    if not app.config.get("TESTING"):
        state_module.app_state = state_module.AppState(
            window_size=app.config["PIPELINE_WINDOW_SIZE"],
            n_subcarriers=app.config["PIPELINE_N_SUBCARRIERS"],
        )
        state_module.app_state.start()
        atexit.register(state_module.app_state.stop)

    return app

__all__ = [
    "CsiLine", "Role", "parse_line",
    "SerialReader", "create_readers",
    "send_settime", "send_reset",
]
