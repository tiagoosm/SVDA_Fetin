import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

from langchain_openai import ChatOpenAI 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# -----------------------------
# CONFIGURAÇÃO INICIAL
# -----------------------------

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializar Flask
app = Flask(__name__)

# Chave secreta usada para criar sessões seguras
app.secret_key = 'sua_chave_secreta_aqui'

# Habilitar CORS para permitir comunicação com frontend de outros domínios
CORS(app, supports_credentials=True)

# Permite enviar caracteres especiais (acentos) no JSON
app.config['JSON_AS_ASCII'] = False

# -----------------------------
# BANCO DE DADOS
# -----------------------------

# Função para criar o banco de dados e tabelas caso não existam
def init_db():
    # Conectar ao banco SQLite (arquivo 'banco.db')
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    # Criar tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- ID único do usuário
            email TEXT UNIQUE NOT NULL,            -- Email do usuário, único
            senha TEXT NOT NULL                     -- Senha criptografada
        )
    ''')

    # Criar tabela de histórico de perguntas/respostas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,    -- ID único do registro
            usuario_id INTEGER,                      -- ID do usuário que enviou a pergunta
            pergunta TEXT,                           -- Pergunta do usuário
            resposta TEXT,                           -- Resposta da IA
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,-- Data/hora da pergunta
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id) -- Relaciona com a tabela usuarios
        )
    ''')

    # Salvar alterações
    conn.commit()
    conn.close()

# Executa a função de inicialização antes de cada requisição
@app.before_request
def setup():
    init_db()

# -----------------------------
# CONFIGURAÇÃO DA IA
# -----------------------------

# Template de instruções para a IA
template = """Você é uma inteligência artificial na qual ajuda produtores de gado, em várias situações na fazenda, mas principalmente na dieta do gado.
 Sua base técnica é o BR-Corte, NASEM e CQBAL 4.0, mas você também pode ajudar o trabalhador rural em outros pontos do dia a dia, como manejo em época de estiagem, saúde e tratamento do gado, orientações práticas de manejo de pasto e organização da fazenda.

Sua comunicação deve ser curta, simples e direta, sem formalidade exagerada, pois você fala com pecuaristas e trabalhadores do campo.
Formular dietas equilibradas.
Ajudar a reduzir custos e melhorar desempenho.
Dar orientações de manejo em estiagem.
Apoiar na saúde e tratamento do gado.
Responder dúvidas do dia a dia da fazenda.

Sempre que responder:

Vá direto ao ponto.

Sugira soluções práticas e, quando possível, traga opções alternativas. Como estaremos trabalhando com pessoas de diversas camadas sociais, como grandes produtores, até produtor de subsistência

Se precisar de mais informações, pergunte de forma simples totas as informações que você precise para conseguir fazer a melhor dieta para o trabalhador ou melhor informação.

Evite palavras técnicas complicadas, mas mantenha precisão técnica.

Histórico da conversa:
{history}

Entrada do usuário:
{input}"""

# Criar prompt para a IA usando histórico de mensagens
prompt = ChatPromptTemplate.from_messages([
    ("system", template),  # Mensagem do sistema definindo comportamento da IA
    MessagesPlaceholder(variable_name="history"),  # Placeholder para histórico
    ("human", "{input}")  # Entrada do usuário
])

# Configurar modelo de IA
llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")  # temperatura controla criatividade

# Cadeia que envia o prompt para a IA
chain = prompt | llm

# -----------------------------
# HISTÓRICO DE SESSÕES
# -----------------------------

# Armazenamento de histórico de cada sessão (usuário)
store = {}

# Função para pegar histórico de uma sessão
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()  # cria novo histórico se não existir
    return store[session_id]

# Cadeia de execução com histórico
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# -----------------------------
# ROTAS DA APLICAÇÃO
# -----------------------------

# Página inicial
@app.route("/")
def home():
    return "Servidor rodando!"

# Rota para registrar novo usuário
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    # Cria hash da senha (não guardar senha em texto puro)
    senha_hash = generate_password_hash(senha)

    try:
        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO usuarios (email, senha) VALUES (?, ?)', (email, senha_hash))
        conn.commit()
        return jsonify({"mensagem": "Usuário registrado com sucesso"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Email já cadastrado"}), 409
    finally:
        conn.close()

# Rota para login do usuário
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, senha FROM usuarios WHERE email = ?', (email,))
    user = cursor.fetchone()  # retorna uma tupla (id, senha)
    conn.close()

    if user and check_password_hash(user[1], senha):
        session['usuario_id'] = user[0]  # cria sessão do usuário
        return jsonify({"mensagem": "Login realizado com sucesso", "session_id": str(user[0])})
    else:
        return jsonify({"erro": "Credenciais inválidas"}), 401

# Rota para enviar mensagem à IA e salvar histórico
@app.route("/mensagem", methods=["POST"])
def responder():
    data = request.get_json()
    pergunta_usuario = data.get("mensagem")
    session_id = data.get("session_id")

    if not pergunta_usuario:
        return jsonify({"erro": "mensagem não fornecida"}), 400

    if not session_id:
        session_id = "usuario_padrao"

    # Envia pergunta para IA considerando histórico da sessão
    resposta = chain_with_history.invoke(
        {"input": pergunta_usuario},
        config={"configurable": {"session_id": session_id}}
    )

    # Tenta salvar pergunta/resposta no banco de dados
    try:
        usuario_id = int(session_id)
        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO historico (usuario_id, pergunta, resposta)
            VALUES (?, ?, ?)
        ''', (usuario_id, pergunta_usuario, resposta.content))
        conn.commit()
        conn.close()
    except:
        pass  # caso não seja possível salvar, ignora

    return jsonify({"resposta": resposta.content})

# Rota para ver histórico do usuário logado
@app.route("/historico", methods=["GET"])
def historico():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT pergunta, resposta, data
        FROM historico
        WHERE usuario_id = ?
        ORDER BY data DESC
    ''', (usuario_id,))
    historico = cursor.fetchall()
    conn.close()

    return jsonify({"historico": [
        {"pergunta": p, "resposta": r, "data": d} for p, r, d in historico
    ]})

# -----------------------------
# EXECUÇÃO DO SERVIDOR
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")  # host 0.0.0.0 permite acesso pela rede
