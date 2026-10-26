"""Configuração lida das variáveis de ambiente (com padrões seguros)."""

import logging
import os
import secrets

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Listas fechadas do cadastro. Só estes valores são aceitos e só eles
# chegam ao prompt (evita injeção de prompt pelos campos do cadastro).
TAMANHOS_REBANHO = {"Pequeno": "pequeno", "Médio": "médio", "Grande": "grande"}
TIPOS_GADO = {"Leite": "de leite", "Corte": "de corte", "Outro": "de outro tipo"}

MAX_PASSWORD_LENGTH = 128
MAX_EMAIL_LENGTH = 254
MAX_NAME_LENGTH = 100

DEV_CORS_ORIGINS = "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5500,http://127.0.0.1:5500"


def env_bool(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    value = os.getenv(name)
    return int(value) if value and value.strip() else default


def resolve_path(path):
    # Caminhos relativos são resolvidos a partir da raiz do projeto, não do cwd
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


def load_config():
    """Monta o dicionário de configuração do Flask a partir do ambiente."""
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
        "DATABASE_PATH": resolve_path(os.getenv("DATABASE_PATH", "banco.db")),
        # Sessão
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
        "SESSION_COOKIE_SECURE": env_bool("SESSION_COOKIE_SECURE", is_production),
        # CORS e proxy reverso
        "CORS_ORIGINS": cors_origins,
        "PROXY_FIX_X_FOR": env_int("PROXY_FIX_X_FOR", 0),
        # Limites de entrada e de custo
        "MIN_PASSWORD_LENGTH": env_int("MIN_PASSWORD_LENGTH", 8),
        "MAX_MESSAGE_CHARS": env_int("MAX_MESSAGE_CHARS", 2000),
        "LLM_MAX_TOKENS": env_int("LLM_MAX_TOKENS", 1024),
        "LLM_TIMEOUT_SECONDS": env_int("LLM_TIMEOUT_SECONDS", 30),
        # Quantas mensagens anteriores da conversa (perguntas + respostas) vão para o modelo
        "HISTORY_MAX_MESSAGES": env_int("HISTORY_MAX_MESSAGES", 10),
        # Rate limiting (sintaxe do Flask-Limiter, ex.: "5 per minute;30 per hour")
        "RATELIMIT_STORAGE_URI": os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        "RATELIMIT_HEADERS_ENABLED": True,
        "RATE_LIMIT_LOGIN": os.getenv("RATE_LIMIT_LOGIN", "5 per minute;30 per hour"),
        "RATE_LIMIT_REGISTER": os.getenv("RATE_LIMIT_REGISTER", "10 per hour"),
        "RATE_LIMIT_MESSAGE": os.getenv("RATE_LIMIT_MESSAGE", "10 per minute;200 per day"),
    }


def validate_config(config):
    """Recusa combinações inseguras antes de o servidor subir."""
    if config["SESSION_COOKIE_SAMESITE"] == "None" and not config["SESSION_COOKIE_SECURE"]:
        raise RuntimeError("SESSION_COOKIE_SAMESITE=None requires SESSION_COOKIE_SECURE=true")
    if "*" in config["CORS_ORIGINS"]:
        raise RuntimeError("CORS_ORIGINS cannot contain '*' because credentials are enabled")
    if config["IS_PRODUCTION"] and not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY is not set; /mensagem will fail until it is configured")
