import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# -----------------------------
# CONFIGURAÇÃO INICIAL
# -----------------------------
load_dotenv()
app = Flask(__name__)
app.secret_key = "sua_chave_secreta_aqui"
CORS(app, supports_credentials=True)
app.config["JSON_AS_ASCII"] = False

# -----------------------------
# BANCO DE DADOS
# -----------------------------
def init_db():
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            pergunta TEXT,
            resposta TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# CONFIGURAÇÃO DA IA
# -----------------------------

template = """ seu nome é assistente SVDA.
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

Histórico da conversa:
{history}

Entrada do usuário:
{input}"""

prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
chain = prompt | llm

store = {}
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# -----------------------------
# ROTAS
# -----------------------------
@app.route("/")
def home():
    return "Servidor rodando!"

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    senha_hash = generate_password_hash(senha)
    try:
        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (email, senha) VALUES (?, ?)", (email, senha_hash))
        conn.commit()
        return jsonify({"mensagem": "Usuário registrado com sucesso"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Email já cadastrado"}), 409
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, senha FROM usuarios WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], senha):
        session["usuario_id"] = user[0]
        return jsonify({"mensagem": "Login realizado com sucesso", "session_id": str(user[0])})
    else:
        return jsonify({"erro": "Credenciais inválidas"}), 401

@app.route("/mensagem", methods=["POST"])
def responder():
    data = request.get_json()
    pergunta_usuario = data.get("mensagem")
    session_id = data.get("session_id") or "usuario_padrao"

    if not pergunta_usuario:
        return jsonify({"erro": "mensagem não fornecida"}), 400

    resposta = chain_with_history.invoke(
        {"input": pergunta_usuario},
        config={"configurable": {"session_id": session_id}}
    )

    texto_resposta = resposta.content  

    try:
        usuario_id = int(session_id)
        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historico (usuario_id, pergunta, resposta)
            VALUES (?, ?, ?)
        """, (usuario_id, pergunta_usuario, texto_resposta))
        conn.commit()
        conn.close()
    except:
        pass

    return jsonify({"resposta": texto_resposta})

@app.route("/historico", methods=["GET"])
def historico():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return jsonify({"erro": "Usuário não autenticado"}), 401

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pergunta, resposta, data
        FROM historico
        WHERE usuario_id = ?
        ORDER BY data DESC
    """, (usuario_id,))
    registros = cursor.fetchall()
    conn.close()

    return jsonify({
        "historico": [
            {"pergunta": p, "resposta": r, "data": d}
            for p, r, d in registros
        ]
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
