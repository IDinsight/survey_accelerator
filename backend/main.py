import logging

import uvicorn
from app import create_app
from app.config import BACKEND_ROOT_PATH
from uvicorn.workers import UvicornWorker

# Configure root logger
logging.basicConfig(
    level=logging.INFO,  # Set to INFO to reduce log verbosity
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Set your application's logger to DEBUG
app_logger = logging.getLogger("app")
app_logger.setLevel(logging.DEBUG)

# Suppress debug logs from third-party libraries
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


app = create_app()


class Worker(UvicornWorker):
    """Custom worker class to allow root_path to be passed to Uvicorn"""

    CONFIG_KWARGS = {"root_path": BACKEND_ROOT_PATH}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
