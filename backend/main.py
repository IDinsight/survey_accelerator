import logging
import os
import sys
from types import FrameType
from typing import Any, Dict, Optional

from app.config import BACKEND_ROOT_PATH
from gunicorn.app.base import BaseApplication
from gunicorn.glogging import Logger
from loguru import logger
from uvicorn.workers import UvicornWorker

LOG_LEVEL = logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO"))
JSON_LOGS = True if os.environ.get("JSON_LOGS", "0") == "1" else False
WORKERS = int(os.environ.get("GUNICORN_WORKERS", "5"))


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging messages and redirect them to Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record.
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame: Optional[FrameType] = sys._getframe(6)
        depth = 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class StubbedGunicornLogger(Logger):
    """
    This class is used to stub out the Gunicorn logger.
    """

    def setup(self, cfg: Any) -> None:
        """
        Setup the logger.
        """
        handler = logging.NullHandler()
        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)
        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)
        self.error_logger.setLevel(LOG_LEVEL)
        self.access_logger.setLevel(LOG_LEVEL)


class Worker(UvicornWorker):
    """Custom worker class to allow root_path to be passed to Uvicorn."""

    CONFIG_KWARGS = {"root_path": BACKEND_ROOT_PATH}


class StandaloneApplication(BaseApplication):
    """Our Gunicorn application."""

    def __init__(self, app: Any, options: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the application with the given app and options.
        """
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self) -> None:
        """
        Load the configuration.
        """
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self) -> Any:
        """
        Load the application.
        """
        return self.application


if __name__ == "__main__":
    intercept_handler = InterceptHandler()
    logging.root.setLevel(LOG_LEVEL)

    seen = set()
    for name in [
        *logging.root.manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    logger.configure(handlers=[{"sink": sys.stdout, "serialize": JSON_LOGS}])

    # Use uvicorn directly with auto-reload
    import uvicorn

    logger.info("Starting server with auto-reload enabled")
    uvicorn.run(
        "app:create_app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=True,
        log_level="info",
    )
