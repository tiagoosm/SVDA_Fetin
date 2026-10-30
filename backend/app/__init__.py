"""SVDA API: application factory."""

import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_config, validate_config
from .db.schema import init_db
from .errors import register_error_handlers
from .extensions import limiter
from .logging_config import register_request_logging, setup_logging
from .routes import auth, conversations, meta


def create_app(overrides=None, llm=None):
    """Create the Flask application.

    overrides: values that replace the configuration read from the environment (tests).
    llm: chat model to use instead of ChatOpenAI (tests).
    """
    load_dotenv()  # reads a .env file, if there is one
    setup_logging(os.getenv("LOG_LEVEL", "INFO"), os.getenv("LOG_FORMAT", "text"))

    config = load_config()
    config.update(overrides or {})
    validate_config(config)

    app = Flask(__name__)
    app.config.update(config)
    app.json.ensure_ascii = False  # keep accents in JSON responses
    if llm is not None:
        app.extensions["svda_llm"] = llm

    # Behind a reverse proxy (nginx), trust N hops of X-Forwarded-For so the
    # rate limiter sees the real client IP.
    if app.config["PROXY_FIX_X_FOR"] > 0:
        hops = app.config["PROXY_FIX_X_FOR"]
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops)

    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)
    limiter.init_app(app)

    app.register_blueprint(meta.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(conversations.bp)

    register_request_logging(app)
    register_error_handlers(app)

    init_db(app.config["DATABASE_PATH"])  # create tables on the first run
    return app
