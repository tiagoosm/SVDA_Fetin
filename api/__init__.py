"""API do SVDA: app factory."""
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_config, validate_config
from .db.schema import init_db
from .extensions import limiter
from .routes import auth, chat, conversations


def create_app(overrides=None, llm=None):
    """Cria a aplicação Flask.

    overrides: valores que substituem a configuração lida do ambiente (testes).
    llm: modelo de chat a usar no lugar do ChatOpenAI (testes).
    """
    load_dotenv()  # Carrega variáveis do arquivo .env
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

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

    @app.route("/")
    def home():
        # Health check público; não expõe dados
        return "Servidor rodando!"

    @app.errorhandler(429)
    def rate_limit_excedido(_error):
        return jsonify({"erro": "Muitas requisições. Aguarde um pouco e tente novamente."}), 429

    init_db(app.config["DATABASE_PATH"])  # Inicializa o banco na primeira execução
    return app
