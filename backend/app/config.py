"""Application configuration, read from environment variables with safe defaults."""

import logging
import os
import secrets

logger = logging.getLogger(__name__)

# The backend directory (backend/). Relative paths in the configuration resolve from here.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Closed lists accepted at sign-up. Only these codes are stored and only their
# phrases reach the prompt, which rules out prompt injection through the profile.
HERD_SIZES = {"small": "pequeno", "medium": "médio", "large": "grande"}
CATTLE_TYPES = {"dairy": "de leite", "beef": "de corte", "other": "de outro tipo"}

MAX_PASSWORD_LENGTH = 128
MAX_EMAIL_LENGTH = 254
MAX_NAME_LENGTH = 100

DEV_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"


def env_bool(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    value = os.getenv(name)
    return int(value) if value and value.strip() else default


def resolve_path(path):
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


def load_config():
    """Build the Flask configuration dictionary from the environment."""
    app_env = os.getenv("APP_ENV", "production").strip().lower()
    is_production = app_env == "production"

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        if is_production:
            raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")
        secret_key = secrets.token_hex(32)
        logger.warning("SECRET_KEY not set; using a random key (sessions are lost on restart)")

    cors_origins = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "" if is_production else DEV_CORS_ORIGINS).split(",")
        if origin.strip()
    ]

    return {
        "APP_ENV": app_env,
        "IS_PRODUCTION": is_production,
        "SECRET_KEY": secret_key,
        "DATABASE_PATH": resolve_path(os.getenv("DATABASE_PATH", "data/svda.db")),
        # Session cookie
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
        "SESSION_COOKIE_SECURE": env_bool("SESSION_COOKIE_SECURE", is_production),
        # CORS and reverse proxy
        "CORS_ORIGINS": cors_origins,
        "PROXY_FIX_X_FOR": env_int("PROXY_FIX_X_FOR", 0),
        # Input and cost limits
        "MIN_PASSWORD_LENGTH": env_int("MIN_PASSWORD_LENGTH", 8),
        "MAX_MESSAGE_CHARS": env_int("MAX_MESSAGE_CHARS", 2000),
        "LLM_MAX_TOKENS": env_int("LLM_MAX_TOKENS", 1024),
        "LLM_TIMEOUT_SECONDS": env_int("LLM_TIMEOUT_SECONDS", 30),
        # How many previous messages (questions + answers) of the conversation reach the model
        "HISTORY_MAX_MESSAGES": env_int("HISTORY_MAX_MESSAGES", 10),
        # Public-demo protection (both off by default)
        "INVITE_CODE": os.getenv("INVITE_CODE", "").strip(),  # required at sign-up when set
        "DAILY_MESSAGE_LIMIT": env_int("DAILY_MESSAGE_LIMIT", 0),  # global per-day cap (UTC); 0 = no cap
        # Rate limiting (Flask-Limiter syntax, e.g. "5 per minute;30 per hour")
        "RATELIMIT_STORAGE_URI": os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        "RATELIMIT_HEADERS_ENABLED": True,
        "RATE_LIMIT_LOGIN": os.getenv("RATE_LIMIT_LOGIN", "5 per minute;30 per hour"),
        "RATE_LIMIT_REGISTER": os.getenv("RATE_LIMIT_REGISTER", "10 per hour"),
        "RATE_LIMIT_MESSAGE": os.getenv("RATE_LIMIT_MESSAGE", "10 per minute;200 per day"),
    }


def validate_config(config):
    """Refuse unsafe combinations before the server starts."""
    if config["SESSION_COOKIE_SAMESITE"] == "None" and not config["SESSION_COOKIE_SECURE"]:
        raise RuntimeError("SESSION_COOKIE_SAMESITE=None requires SESSION_COOKIE_SECURE=true")
    if "*" in config["CORS_ORIGINS"]:
        raise RuntimeError("CORS_ORIGINS cannot contain '*' because credentials are enabled")
    if config["IS_PRODUCTION"] and not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY is not set; sending messages will fail until it is configured")
