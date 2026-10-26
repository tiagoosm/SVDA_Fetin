# ==============================
# BIBLIOTECAS
# ==============================
import logging                                # Logs da aplicação
import os                                     # Variáveis de ambiente e caminhos de arquivos
import re                                     # Validação de e-mail
import secrets                                # Chave aleatória em desenvolvimento
import sqlite3                                # Banco de dados SQLite
import uuid                                   # IDs de conversa
from contextlib import closing
from functools import wraps

from dotenv import load_dotenv                # Para carregar variáveis de ambiente (.env)
from flask import Flask, g, jsonify, request, session  # Framework web para criar a API
from flask_cors import CORS                   # Libera acesso apenas das origens permitidas
from flask_limiter import Limiter             # Rate limiting
from flask_limiter.util import get_remote_address
from openai import OpenAIError                # Erros da API da OpenAI
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash  # Hash de senhas
from langchain_openai import ChatOpenAI       # Integração com modelo OpenAI
from langchain_core.messages import AIMessage, HumanMessage  # Mensagens do histórico
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # Construção de prompt

# ==============================
# CONFIGURAÇÃO
# ==============================
load_dotenv()  # Carrega variáveis do arquivo .env

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("svda")


def env_bool(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_int(name, default):
    value = os.getenv(name)
    return int(value) if value and value.strip() else default


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ambiente: "production" (padrão seguro), "development" ou "testing"
APP_ENV = os.getenv("APP_ENV", "production").strip().lower()
IS_PRODUCTION = APP_ENV == "production"

# Limites de entrada e de custo
MIN_PASSWORD_LENGTH = env_int("MIN_PASSWORD_LENGTH", 8)
MAX_PASSWORD_LENGTH = 128
MAX_EMAIL_LENGTH = 254
MAX_MESSAGE_CHARS = env_int("MAX_MESSAGE_CHARS", 2000)
LLM_MAX_TOKENS = env_int("LLM_MAX_TOKENS", 1024)
# Quantas mensagens anteriores da conversa (perguntas + respostas) vão para o modelo
HISTORY_MAX_MESSAGES = env_int("HISTORY_MAX_MESSAGES", 10)
MAX_NAME_LENGTH = 100

# Listas fechadas do cadastro. Só estes valores são aceitos e só eles
# chegam ao prompt (evita injeção de prompt pelos campos do cadastro).
TAMANHOS_REBANHO = {"Pequeno": "pequeno", "Médio": "médio", "Grande": "grande"}
TIPOS_GADO = {"Leite": "de leite", "Corte": "de corte", "Outro": "de outro tipo"}

# Rate limiting (sintaxe do Flask-Limiter, ex.: "5 per minute;30 per hour")
RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "5 per minute;30 per hour")
RATE_LIMIT_REGISTER = os.getenv("RATE_LIMIT_REGISTER", "10 per hour")
RATE_LIMIT_MESSAGE = os.getenv("RATE_LIMIT_MESSAGE", "10 per minute;200 per day")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ==============================
# CONFIGURAÇÃO FLASK
# ==============================
app = Flask(__name__)
app.json.ensure_ascii = False  # Permite caracteres UTF-8 (acentos no JSON)

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    if IS_PRODUCTION:
        raise RuntimeError("SECRET_KEY must be set when APP_ENV=production")
    secret_key = secrets.token_hex(32)
    logger.warning("SECRET_KEY not set; using a random key (sessions are lost on restart)")
app.secret_key = secret_key

app.config.update(
    DATABASE_PATH=os.getenv("DATABASE_PATH", os.path.join(BASE_DIR, "banco.db")),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
    SESSION_COOKIE_SECURE=env_bool("SESSION_COOKIE_SECURE", IS_PRODUCTION),
)
if app.config["SESSION_COOKIE_SAMESITE"] == "None" and not app.config["SESSION_COOKIE_SECURE"]:
    raise RuntimeError("SESSION_COOKIE_SAMESITE=None requires SESSION_COOKIE_SECURE=true")

# Atrás de um proxy reverso (nginx), confia em N saltos de X-Forwarded-For
# para que o rate limiting enxergue o IP real do cliente.
proxy_hops = env_int("PROXY_FIX_X_FOR", 0)
if proxy_hops > 0:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=proxy_hops, x_proto=proxy_hops)

# CORS: somente origens listadas em CORS_ORIGINS (separadas por vírgula)
DEV_CORS_ORIGINS = (
    "http://localhost:8080,http://127.0.0.1:8080,"
    "http://localhost:5500,http://127.0.0.1:5500"
)
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "" if IS_PRODUCTION else DEV_CORS_ORIGINS).split(",")
    if origin.strip()
]
if "*" in cors_origins:
    raise RuntimeError("CORS_ORIGINS cannot contain '*' because credentials are enabled")
CORS(app, origins=cors_origins, supports_credentials=True)


def rate_limit_user_key():
    # Usuário autenticado é limitado pelo ID; sem sessão, pelo IP
    usuario_id = session.get("usuario_id")
    return f"user:{usuario_id}" if usuario_id else get_remote_address()


limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    headers_enabled=True,
)

# ===============================
# BANCO DE DADOS
# ===============================

def get_connection():
    return sqlite3.connect(app.config["DATABASE_PATH"])


def init_db():
   # Cria tabelas caso ainda não existam
    with closing(get_connection()) as conn, conn:
        cursor = conn.cursor()

        # Tabela de usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                nome TEXT,
                tamanho_rebanho TEXT,
                tipo_gado TEXT
            )
        """)

        # Migração para bancos criados antes dos campos de perfil (idempotente)
        colunas = {row[1] for row in cursor.execute("PRAGMA table_info(usuarios)")}
        for coluna in ("nome", "tamanho_rebanho", "tipo_gado"):
            if coluna not in colunas:
                cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {coluna} TEXT")
                logger.info("Database migrated: added usuarios.%s", coluna)

        # Tabela de histórico de conversas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                conversa_id TEXT,
                pergunta TEXT,
                resposta TEXT,
                data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
            )
        """)

# Inicializa o banco na primeira execução
init_db()

# ==============================
# TEMPLATE DO ASSISTENTE (PROMPT)
# ==============================
# Esse texto define como a IA deve se comportar

template = """ seu nome é assistente SVDAB.
Você é uma inteligência artificial especialista em pecuária, criada para apoiar produtores de gado de corte e leite, em propriedades grandes, médias ou pequenas.
Seu foco principal é nutrição, saúde e manejo, mas você também deve orientar em organização da fazenda e dúvidas do dia a dia.

- Estilo de comunicação

Fale de forma simples, curta e direta, como se estivesse conversando com um trabalhador rural.

Evite termos complicados, mas não perca a precisão técnica.

Use frases curtas, listas e comparações práticas.

Vá direto ao ponto sempre que responder.

Se não tiver informação suficiente, pergunte de forma clara e curta.

Sempre que possível, ofereça duas ou mais opções: uma simples/barata e outra mais completa/tecnificada.

- Bases técnicas que sustentam seu conhecimento
1. Nutrição de Bovinos de Corte (BR-Corte / Embrapa)

Você domina todos os conceitos do BR-Corte, com base em exigências nutricionais e práticas de manejo:

Suplementação a pasto:

Sal mineral simples: repõe minerais básicos.

Suplementos ureado-proteicos: fornecem nitrogênio não proteico na seca.

Proteinado múltiplo: mistura de energia + proteína + minerais, aumenta ganhos mesmo em pasto de baixa qualidade.

Semiconfinamento:

Fornecimento de 0,5% a 1% do PV em concentrado (milho, soja, polpa cítrica, caroço de algodão etc.) no cocho.

Pasto continua sendo a principal fonte de volumoso.

Confinamento:

Dietas com até 80% de concentrado.

Necessidade de adaptação lenta para evitar acidose.

Uso de aditivos como monensina e virginiamicina para melhorar conversão alimentar.

Princípios gerais:

Um boi de 400 kg precisa de 8 a 10 kg de matéria seca por dia.

Ganho de 1,2 a 1,5 kg/dia exige dietas de 12–14% PB e 65–70% NDT.

Manejo de cocho, espaço adequado (60 cm/animal), água limpa e adaptação são fundamentais.

2. Nutrição de Bovinos de Leite (Emater-MG – Nutrição e Manejo Alimentar)

Volumosos: capim (napier, mombaça, braquiária), silagem de milho, sorgo, cana, feno.

Concentrados: milho moído, farelo de soja, trigo, caroço de algodão.

Minerais: cálcio, fósforo, sódio, enxofre, microminerais.

Vitaminas: A, D e E, principalmente em confinamento.

Regras práticas:

Vacas de alta produção: até 60% concentrado, 40% volumoso.

Vacas de média produção: 30 a 40% concentrado.

Proporção depende da qualidade do pasto/volumoso.

Água: vaca produzindo 20 L de leite bebe 60–80 L/dia.

Exigências aproximadas:

Vacas de 20 L/dia: 16% PB e 65% NDT na dieta.

Vacas de 30 L/dia: 17–18% PB e 68–70% NDT.

Fases da lactação:

Início: ajustar para evitar perda de peso.

Pico: manter aporte energético alto.

Fim: reduzir concentrado, dar mais volumoso.

Manejo: separar vacas por produção, evitar superlotação de cocho, fornecer suplemento na ordenha.

3. Alimentos para Gado de Leite (UFMG – FEPMVZ)

Esse livro detalha a classificação dos alimentos e como aproveitá-los:

Volumosos: capim-elefante, cana, napier, silagem de milho, sorgo, girassol, milheto, mandioca forrageira.

Concentrados energéticos: milho, sorgo, trigo, polpa cítrica, polpa de beterraba, resíduos de cervejaria, mandioca.

Concentrados proteicos: soja, caroço de algodão, girassol, amendoim, glúten de milho.

Resíduos agroindustriais: bagaço de cana hidrolisado, casca de soja, polpa de frutas, resíduos de panificação, subprodutos de oleaginosas.

Suplementos minerais: fósforo, cálcio, enxofre, sódio, microminerais.

Aditivos: ureia (até 1% da MS total), monensina, tamponantes, probióticos.

Pontos críticos:

Forrageiras perdem qualidade se cortadas muito tarde (mais fibra, menos proteína).

Mistura de resíduos pode reduzir custo sem cair desempenho.

Sempre que possível, fazer análise bromatológica.

4. Vacinação e Saúde Animal (Embrapa – Boas Práticas)

Vacinas obrigatórias:

Febre aftosa: todo o rebanho, conforme calendário oficial.

Brucelose: fêmeas de 3 a 8 meses, apenas uma vez, com registro oficial.

Raiva: em áreas de risco, todo o rebanho.

Vacinas recomendadas:

Clostridioses (botulismo, carbúnculo, enterotoxemia).

Leptospirose.

IBR e BVD (doenças reprodutivas e respiratórias).

Boas práticas de vacinação:

Armazenar entre 2 °C e 8 °C, nunca congelar.

Transportar em caixa térmica com gelo.

Trocar agulha a cada 10 animais.

Usar seringas limpas e calibradas.

Manejar o gado com calma para reduzir estresse.

Registrar datas, reforços e lotes vacinados.

Descartar corretamente frascos e agulhas.

5. Manejo em épocas críticas

Na seca:

Pasto perde proteína → usar ureia, proteinados múltiplos ou silagem.

Fornecer suplementação mineral com enxofre.

Água sempre disponível.

Nas águas:

Capim é abundante, mas pobre em minerais.

Usar sal mineral completo.

Controlar parasitas externos e internos.

6. Saúde, bem-estar e boas práticas

Água: sempre limpa e fresca, bebedouros bem localizados.

Cocho: espaço adequado, cocho coberto no confinamento.

Bem-estar: sombra natural ou artificial, manejo calmo, evitar lotação excessiva.

Parasitas: controle de carrapatos, vermes e moscas.

Organização: manter registros simples de dieta, ganho, vacinas e saúde.

- Suas funções principais

Formular dietas equilibradas (corte e leite).

Ajustar alimentação ao custo e disponibilidade.

Recomendar manejo na seca e nas águas.

Dar apoio em saúde, vacinação e prevenção.

Responder dúvidas práticas do produtor.

Sempre trazer opções alternativas (simples/barata x completa/tecnificada).

- Como você deve sempre responder

Vá direto ao ponto.

Use frases simples e listas.

Se não tiver dados suficientes, pergunte.

Ofereça pelo menos duas opções sempre que possível.

Nunca complique com linguagem técnica.

- Perguntas que você deve sempre fazer ao produtor

Seu gado é de corte ou de leite?

Qual a categoria dos animais (bezerros, novilhas, vacas em lactação, bois de engorda etc.)?

Qual o peso médio dos animais ou a produção de leite por vaca/dia?

Qual o objetivo? (engorda, ganho rápido, mais leite, manter rebanho na seca etc.)

Quais alimentos você tem disponíveis na fazenda? (capim, silagem, cana, milho, soja, resíduos, sal mineral etc.)

Quer que eu considere algum limite de custo por animal/dia?

Tem alguma restrição? (sem ureia, sem aditivos, sem concentrados caros etc.)

Deseja também orientações sobre o calendário de vacinação?

- Exemplos práticos de uso

“Tenho bois de 400 kg no pasto na seca. Quero engorda rápida.”

“Minhas vacas estão produzindo 20 litros de leite/dia. Tenho milho e soja.”

“Preciso de dieta barata só para manter as vacas até a chuva chegar.”

“Quero saber quais vacinas são obrigatórias para bezerros.”

Suas orientações não substituem a avaliação de um médico-veterinário ou zootecnista; lembre o produtor disso quando o caso exigir atendimento profissional.
{contexto_produtor}"""

# ==============================
# CONFIGURAÇÃO DO LLM (IA)
# ==============================

prompt = ChatPromptTemplate.from_messages([
    ("system", template),              # Mensagem inicial (contexto fixo)
    MessagesPlaceholder(variable_name="history"),  # Histórico da conversa
    ("human", "{input}")               # Entrada do usuário
])

# Modelo OpenAI usado (GPT-4o-mini). max_tokens limita o custo de cada resposta.

llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini", max_tokens=LLM_MAX_TOKENS)


def gerar_resposta(pergunta, historico, contexto_produtor=""):
    # Junta o prompt com o modelo e faz UMA chamada ao LLM
    chain = prompt | llm
    resposta = chain.invoke({
        "input": pergunta,
        "history": historico,
        "contexto_produtor": contexto_produtor,
    })
    return resposta.content

# ==============================
# GERENCIAMENTO DE HISTÓRICO
# ==============================
# A memória é por (usuário, conversa) e é reconstruída a partir da tabela
# historico, então sobrevive a reinícios do servidor. Só as últimas
# HISTORY_MAX_MESSAGES mensagens são enviadas ao modelo (controle de custo).

def carregar_historico(usuario_id, conversa_id, limite=None):
    limite = HISTORY_MAX_MESSAGES if limite is None else limite
    if limite <= 0:
        return []
    pares = (limite + 1) // 2  # Cada registro tem uma pergunta e uma resposta
    with closing(get_connection()) as conn:
        registros = conn.execute("""
            SELECT pergunta, resposta
            FROM historico
            WHERE usuario_id = ? AND conversa_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (usuario_id, conversa_id, pares)).fetchall()

    mensagens = []
    for pergunta, resposta in reversed(registros):
        mensagens.append(HumanMessage(content=pergunta or ""))
        mensagens.append(AIMessage(content=resposta or ""))
    return mensagens[-limite:]


def contexto_do_produtor(usuario_id):
    # Monta a linha de contexto apenas a partir das listas fechadas
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT tamanho_rebanho, tipo_gado FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
    if not row:
        return ""
    porte = TAMANHOS_REBANHO.get(row[0])
    tipo = TIPOS_GADO.get(row[1])
    if not porte or not tipo:
        return ""
    return f"O produtor tem rebanho {tipo}, de porte {porte}."

# ==============================
# AUTENTICAÇÃO E VALIDAÇÃO
# ==============================

# Hash usado quando o e-mail não existe, para o tempo de resposta do login
# não revelar quais e-mails estão cadastrados.
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_hex(16))


def login_required(view):
    # O usuário vem SEMPRE da sessão assinada no servidor, nunca do cliente
    @wraps(view)
    def wrapper(*args, **kwargs):
        usuario_id = session.get("usuario_id")
        if not isinstance(usuario_id, int):
            return jsonify({"erro": "Usuário não autenticado"}), 401
        g.usuario_id = usuario_id
        return view(*args, **kwargs)
    return wrapper


def json_body():
    # Exige JSON (Content-Type: application/json), o que também força o
    # preflight de CORS em requisições vindas de outras origens.
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def validar_credenciais(data):
    email = data.get("email")
    senha = data.get("senha")
    if not isinstance(email, str) or not isinstance(senha, str) or not email.strip() or not senha:
        return None, None, "Email e senha são obrigatórios"
    email = email.strip()
    if len(email) > MAX_EMAIL_LENGTH or not EMAIL_RE.match(email):
        return None, None, "Email inválido"
    if len(senha) > MAX_PASSWORD_LENGTH:
        return None, None, f"A senha deve ter no máximo {MAX_PASSWORD_LENGTH} caracteres"
    return email, senha, None


def validar_perfil(data):
    nome = data.get("nome")
    tamanho = data.get("tamanho_rebanho")
    tipo = data.get("tipo_gado")
    if not isinstance(nome, str) or not nome.strip():
        return None, "Nome é obrigatório"
    if len(nome.strip()) > MAX_NAME_LENGTH:
        return None, f"O nome deve ter no máximo {MAX_NAME_LENGTH} caracteres"
    if tamanho not in TAMANHOS_REBANHO:
        return None, "Tamanho do rebanho inválido"
    if tipo not in TIPOS_GADO:
        return None, "Tipo de gado inválido"
    return {"nome": nome.strip(), "tamanho_rebanho": tamanho, "tipo_gado": tipo}, None


def conversa_id_valido(valor):
    try:
        return str(uuid.UUID(valor)) == valor.lower()
    except (ValueError, AttributeError, TypeError):
        return False


@app.errorhandler(429)
def rate_limit_excedido(_error):
    return jsonify({"erro": "Muitas requisições. Aguarde um pouco e tente novamente."}), 429

# ==============================
# ROTAS FLASK
# ==============================

@app.route("/")
def home():

    # Health check público; não expõe dados

    return "Servidor rodando!"

# ------------------------------
# Registro de usuário
# ------------------------------

@app.route("/register", methods=["POST"])
@limiter.limit(RATE_LIMIT_REGISTER)
def register():
    data = json_body()
    if data is None:
        return jsonify({"erro": "Requisição inválida"}), 400

    email, senha, erro = validar_credenciais(data)
    if erro:
        return jsonify({"erro": erro}), 400
    if len(senha) < MIN_PASSWORD_LENGTH:
        return jsonify({"erro": f"A senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres"}), 400
    perfil, erro = validar_perfil(data)
    if erro:
        return jsonify({"erro": erro}), 400

    senha_hash = generate_password_hash(senha)  # Cria hash da senha
    try:
        with closing(get_connection()) as conn, conn:
            conn.execute(
                "INSERT INTO usuarios (email, senha, nome, tamanho_rebanho, tipo_gado) VALUES (?, ?, ?, ?, ?)",
                (email, senha_hash, perfil["nome"], perfil["tamanho_rebanho"], perfil["tipo_gado"]),
            )
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Email já cadastrado"}), 409
    return jsonify({"mensagem": "Usuário registrado com sucesso"}), 201

# ------------------------------
# Login
# ------------------------------

@app.route("/login", methods=["POST"])
@limiter.limit(RATE_LIMIT_LOGIN)
def login():
    data = json_body()
    if data is None:
        return jsonify({"erro": "Requisição inválida"}), 400

    email, senha, erro = validar_credenciais(data)
    if erro:
        return jsonify({"erro": erro}), 400

    with closing(get_connection()) as conn:
        user = conn.execute("SELECT id, senha FROM usuarios WHERE email = ?", (email,)).fetchone()

    # Verifica senha (sempre calcula um hash, exista o usuário ou não)
    senha_ok = check_password_hash(user[1] if user else DUMMY_PASSWORD_HASH, senha)
    if not (user and senha_ok):
        logger.info("Failed login attempt from %s", get_remote_address())
        return jsonify({"erro": "Credenciais inválidas"}), 401

    session.clear()  # Evita fixação de sessão
    session["usuario_id"] = user[0]
    return jsonify({"mensagem": "Login realizado com sucesso"})

# ------------------------------
# Logout e usuário atual
# ------------------------------

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    return jsonify({"mensagem": "Logout realizado com sucesso"})


@app.route("/me", methods=["GET"])
@login_required
def me():
    with closing(get_connection()) as conn:
        user = conn.execute(
            "SELECT id, email, nome, tamanho_rebanho, tipo_gado FROM usuarios WHERE id = ?",
            (g.usuario_id,),
        ).fetchone()
    if not user:
        session.clear()
        return jsonify({"erro": "Usuário não autenticado"}), 401
    return jsonify({
        "usuario_id": user[0],
        "email": user[1],
        "nome": user[2],
        "tamanho_rebanho": user[3],
        "tipo_gado": user[4],
    })

# ------------------------------
# Enviar mensagem ao chatbot
# ------------------------------

@app.route("/mensagem", methods=["POST"])
@login_required
@limiter.limit(RATE_LIMIT_MESSAGE, key_func=rate_limit_user_key)
def responder():
    data = json_body()
    if data is None:
        return jsonify({"erro": "Requisição inválida"}), 400

    usuario_id = g.usuario_id
    pergunta_usuario = data.get("mensagem")
    conversa_id = data.get("conversa_id") or str(uuid.uuid4())  # Cria ID da conversa se não tiver

    if not isinstance(pergunta_usuario, str) or not pergunta_usuario.strip():
        return jsonify({"erro": "mensagem não fornecida"}), 400
    pergunta_usuario = pergunta_usuario.strip()
    if len(pergunta_usuario) > MAX_MESSAGE_CHARS:
        return jsonify({"erro": f"A mensagem deve ter no máximo {MAX_MESSAGE_CHARS} caracteres"}), 400
    if not conversa_id_valido(conversa_id):
        return jsonify({"erro": "conversa_id inválido"}), 400

    # Chama o modelo com o histórico desta conversa (últimas N mensagens)
    try:
        texto_resposta = gerar_resposta(
            pergunta_usuario,
            carregar_historico(usuario_id, conversa_id),
            contexto_do_produtor(usuario_id),
        )
    except OpenAIError:
        logger.exception("LLM request failed (user_id=%s)", usuario_id)
        return jsonify({"erro": "O assistente está indisponível no momento. Tente novamente em instantes."}), 502

    # Salva no banco
    try:
        with closing(get_connection()) as conn, conn:
            conn.execute("""
                INSERT INTO historico (usuario_id, conversa_id, pergunta, resposta)
                VALUES (?, ?, ?, ?)
            """, (usuario_id, conversa_id, pergunta_usuario, texto_resposta))
    except sqlite3.Error:
        logger.exception("Failed to save message history (user_id=%s)", usuario_id)

    return jsonify({"resposta": texto_resposta, "conversa_id": conversa_id})

# ------------------------------
# Listar conversas de um usuário
# ------------------------------

@app.route("/conversas", methods=["GET"])
@login_required
def listar_conversas():
    usuario_id = g.usuario_id

    with closing(get_connection()) as conn:
        registros = conn.execute("""
            SELECT h.conversa_id, h.pergunta, h.resposta, h.data
            FROM historico h
            JOIN (
                SELECT MIN(id) AS primeiro_id
                FROM historico
                WHERE usuario_id = ?
                GROUP BY conversa_id
            ) p ON h.id = p.primeiro_id
            WHERE h.usuario_id = ?
            ORDER BY h.id DESC
        """, (usuario_id, usuario_id)).fetchall()

    # Monta resposta resumida

    conversas = []
    for conversa_id, pergunta, resposta, data in registros:
        titulo = (pergunta[:40] + "...") if pergunta else "Conversa"
        previa = (resposta[:80] + "...") if resposta else ""
        conversas.append({
            "conversa_id": conversa_id,
            "titulo": titulo,
            "previa": previa,
            "data": data
        })

    return jsonify({"conversas": conversas})

# ------------------------------
# Histórico de uma conversa
# ------------------------------

@app.route("/historico", methods=["GET"])
@login_required
def historico():
    usuario_id = g.usuario_id
    conversa_id = request.args.get("conversa_id")

    with closing(get_connection()) as conn:
        # Busca histórico específico ou todos
        if conversa_id:
            registros = conn.execute("""
                SELECT pergunta, resposta, data
                FROM historico
                WHERE usuario_id = ? AND conversa_id = ?
                ORDER BY id ASC
            """, (usuario_id, conversa_id)).fetchall()
        else:
            registros = conn.execute("""
                SELECT pergunta, resposta, data
                FROM historico
                WHERE usuario_id = ?
                ORDER BY id ASC
            """, (usuario_id,)).fetchall()

    return jsonify({
        "historico": [
            {"pergunta": p, "resposta": r, "data": d}
            for p, r, d in registros
        ]
    })

# ==============================
# EXECUÇÃO DO SERVIDOR
# ==============================

if __name__ == "__main__":
    debug = env_bool("FLASK_DEBUG", False)
    if debug and IS_PRODUCTION:
        raise RuntimeError("FLASK_DEBUG cannot be enabled when APP_ENV=production")
    app.run(
        host=os.getenv("FLASK_RUN_HOST", "127.0.0.1"),
        port=env_int("PORT", 5000),
        debug=debug,
    )
