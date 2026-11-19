"""
Initialize the app

Create an application factory function, which will be used to create a new app instance.

docs: https://flask.palletsprojects.com/en/2.3.x/patterns/appfactories/
"""

import re

from flask_cors import CORS
from flask import Flask
from flask_socketio import SocketIO
from logging.config import dictConfig

from director.entrypoint.api.routes import session_bp, videodb_bp, config_bp
from director.entrypoint.api.socket_io import ChatNamespace

from dotenv import load_dotenv

load_dotenv()

socketio = SocketIO()

# Without SERVER_ALLOWED_ORIGINS, only pages served from this machine may call the API.
LOOPBACK_ORIGIN = r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$"


def allowed_origins(value) -> list:
    """SERVER_ALLOWED_ORIGINS as a list; it arrives as a string, or a list when it is JSON."""
    if isinstance(value, str):
        value = value.split(",")
    return [str(origin).strip() for origin in value or [] if str(origin).strip()]


def origin_check(origins: list):
    """The CORS rule for both Flask and the chat socket."""
    if "*" in origins:
        return "*", "*"
    if not origins:
        loopback = re.compile(LOOPBACK_ORIGIN)
        return [LOOPBACK_ORIGIN], lambda origin: bool(origin and loopback.match(origin))
    return origins, origins


def create_app(app_config: object):
    """
    Create a Flask app using the app factory pattern.

    :param app_config: The configuration object to use.
    :return: A Flask app.
    """
    app = Flask(__name__)

    # Set the app config
    app.config.from_object(app_config)
    app.config.from_prefixed_env(app_config.ENV_PREFIX)
    http_origins, socket_origins = origin_check(
        allowed_origins(app.config["ALLOWED_ORIGINS"])
    )
    CORS(app, origins=http_origins)

    # Init the socketio and attach it to the app
    socketio.init_app(
        app,
        cors_allowed_origins=socket_origins,
        logger=True,
        engineio_logger=True,
        reconnection=False if app.config["DEBUG"] else True,
    )
    app.socketio = socketio

    # Set the logging config
    dictConfig(app.config["LOGGING_CONFIG"])

    with app.app_context():
        from director.entrypoint.api import errors

    # register blueprints
    app.register_blueprint(session_bp)
    app.register_blueprint(videodb_bp)
    app.register_blueprint(config_bp)

    # register socket namespaces
    socketio.on_namespace(ChatNamespace("/chat"))

    return app
