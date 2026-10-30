"""Development server: python -m app"""

import os

from dotenv import load_dotenv

from . import create_app
from .config import env_bool, env_int

load_dotenv()
app = create_app()

if __name__ == "__main__":
    debug = env_bool("FLASK_DEBUG", False)
    if debug and app.config["IS_PRODUCTION"]:
        raise RuntimeError("FLASK_DEBUG cannot be enabled when APP_ENV=production")
    app.run(
        host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
        port=env_int("PORT", 5000),
        debug=debug,
    )
