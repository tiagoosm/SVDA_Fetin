"""API do SVDA: app factory."""

import os

from dotenv import load_dotenv
from flask import Flask, Response, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import BASE_DIR, load_config, validate_config
from .db.schema import init_db
from .errors import register_error_handlers
from .extensions import limiter
from .logging_config import register_request_logging, setup_logging
from .routes import auth, chat, conversations

INTERFACE_DIR = os.path.join(BASE_DIR, "interface")


def register_frontend(app):
    """Serve o frontend estático (interface/) na mesma origem da API."""

    @app.route("/config.js")
    def frontend_config():
        # Mesma origem: a API fica na raiz, sem prefixo
        return Response("window.SVDA_CONFIG = { API_BASE: '' };\n", mimetype="text/javascript")

    @app.route("/")
    def index():
        return send_from_directory(INTERFACE_DIR, "index.html")

    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory(INTERFACE_DIR, filename)


def create_app(overrides=None, llm=None):
    """Cria a aplicação Flask.

    overrides: valores que substituem a configuração lida do ambiente (testes).
    llm: modelo de chat a usar no lugar do ChatOpenAI (testes).
    """
    load_dotenv()  # Carrega variáveis do arquivo .env
    setup_logging(os.getenv("LOG_LEVEL", "INFO"), os.getenv("LOG_FORMAT", "text"))

    config = load_config()
    config.update(overrides or {})
    validate_config(config)

    app = Flask(__name__)
    app.config.update(config)
    app.json.ensure_ascii = False  # Permite caracteres UTF-8 (acentos no JSON)
    if llm is not None:
        app.extensions["svda_llm"] = llm

    # Atrás de um proxy reverso (nginx), confia em N saltos de X-Forwarded-For
    # para que o rate limiting enxergue o IP real do cliente.
    if app.config["PROXY_FIX_X_FOR"] > 0:
        hops = app.config["PROXY_FIX_X_FOR"]
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=hops)

    # CORS: somente origens listadas em CORS_ORIGINS
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)
    limiter.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    app.register_blueprint(conversations.bp)

    @app.route("/healthz")
    def healthz():
        # Health check público; não expõe dados
        return "ok"

    if app.config["SERVE_FRONTEND"]:
        register_frontend(app)
    else:

        @app.route("/")
        def home():
            return "Servidor rodando!"

    register_request_logging(app)
    register_error_handlers(app)

    init_db(app.config["DATABASE_PATH"])  # Inicializa o banco na primeira execução
    return app
