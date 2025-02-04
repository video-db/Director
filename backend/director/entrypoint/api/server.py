import os

from dotenv import load_dotenv
from director.entrypoint.api import create_app

load_dotenv()


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "engineio": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}


class BaseAppConfig:
    """Base configuration for the app."""

    DEBUG: bool = 1
    """Debug mode for the app."""
    TESTING: bool = 1
    """Testing mode for the app."""
    SECRET_KEY: str = "secret"
    """Secret key for the app."""
    LOGGING_CONFIG: dict = LOGGING_CONFIG
    """Logging configuration for the app."""
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")
    """Database type for the app."""
    HOST: str = "0.0.0.0"
    """Host for the app."""
    PORT: int = 8000
    """Port for the app."""
    ENV_PREFIX: str = "SERVER"


class LocalAppConfig(BaseAppConfig):
    """Local configuration for the app. All the default values can be change using environment variables. e.g. `SERVER_PORT=8001`"""

    TESTING: bool = 0
    """Testing mode for the app."""


class ProductionAppConfig(BaseAppConfig):
    """Production configuration for the app. All the default values can be change using environment variables. e.g. SERVER_PORT=8001"""

    DEBUG: bool = 0
    """Debug mode for the app."""
    TESTING: bool = 0
    """Testing mode for the app."""
    SECRET_KEY: str = "production"
    """Secret key for the app."""


configs = dict(local=LocalAppConfig, production=ProductionAppConfig)


# By default, the server is configured to run in development mode. To run in production mode, set the `SERVER_ENV` environment variable to `production`.
app = create_app(app_config=configs[os.getenv("SERVER_ENV", "local")])

if os.getenv("DEVZERY_API_KEY") and os.getenv("DEVZERY_SOURCE_NAME"):
    from devzery import Devzery
    devzery = Devzery(
        api_key=os.getenv("DEVZERY_API_KEY"),
        source_name=os.getenv("DEVZERY_SOURCE_NAME")
    )

    devzery.flask_middleware(app)

if __name__ == "__main__":
    app.run(
        host=os.getenv("SERVER_HOST", app.config["HOST"]),
        port=os.getenv("SERVER_PORT", app.config["PORT"]),
        reloader_type="stat",
    )
