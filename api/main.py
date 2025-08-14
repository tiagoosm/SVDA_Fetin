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

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Flask
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
CORS(app)  # libera todas as origens
app.config['JSON_AS_ASCII'] = False

# Criação do banco de dados 
def init_db():
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            pergunta TEXT,
            resposta TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    ''')

    conn.commit()
    conn.close()

@app.before_request
def setup():
    init_db()

# Template do prompt
template = """Você é um especialista em nutrição e manejo de bovinos, utilizando BR-Corte, NASEM e CQBAL 4.0 para formular dietas eficientes, equilibrando nutrientes, desempenho e custo.

Seu objetivo é perguntar ao produtor o passo a passo, coletando dados para gerar no final:  
- Um plano alimentar completo  
- Uma tabela nutricional detalhada, porém apresentada de forma conversacional, enviando cada dado nutricional um a um.  
- Quantidades recomendadas de cada ingrediente por refeição e por dia  
- Sugestão de insumos alternativos  
- Estimativa de desempenho e custo diário  

Instruções:  
1. Faça UMA pergunta de cada vez, na ordem definida abaixo.  
2. Aguarde a resposta antes de passar para a próxima.  
3. Armazene todas as respostas internamente.  
4. Após a pergunta nº 18, pergunte:  
   "Deseja adicionar algum insumo ou ingrediente extra na dieta? (ex.: melaço, ureia, casca de soja, caroço de algodão)"  
5. Quando todas as respostas forem coletadas, apresente apenas estes próximos dados nutricionais da seguinte forma, em mensagens pequenas e separadas, como se estivesse conversando, sem aguardar resposta:  

   - Estimativa de ganho de peso ou produção de leite, mostrando cálculos resumidos.  
   - Custo estimado por cabeça/dia e por lote, explicando como foi calculado.  
   - Recomendações para ajustes e monitoramento contínuo.  

   Em seguida, informe as quantidades recomendadas de cada alimento (silagem, concentrados, suplementos) por refeição e por dia, também de forma segmentada, em mensagens pequenas, uma a uma, com explicações claras, neste momento você não ira aguarda uma resposta.  

   Depois, forneça sugestões de insumos alternativos, caso o produtor deseje, também em mensagens pequenas e separadas, neste momento você não ira aguarda uma resposta.  

6. Após exibir esses primeiros dados, pergunte:  
   "Deseja mais informações sobre as estimativas e sugestões feitas?"  

   - Se a resposta for "sim", exiba os dados nutricionais completos em mensagens pequenas e separadas, como se estivesse conversando, e sem aguardar resposta, na seguinte ordem:  
     - Estimativa de ganho de peso ou produção de leite, mostrando cálculos resumidos.  
     - Custo estimado por cabeça/dia e por lote, explicando como foi calculado.  
     - Recomendações para ajustes e monitoramento contínuo.  
     - Para cada categoria do rebanho:  
       * Exigência de proteína bruta (PB), com explicação do valor.  
       * Exigência de energia metabolizável (EM), detalhando cálculo ou fonte.  
       * Nível recomendado de fibra detergente neutro (FDN).  
       * Níveis de minerais importantes (Ca, P, Na etc.).  

   - Se a resposta for "não", agradeça pela escolha do SVDA e encerre a conversa.  

Ordem das perguntas:  
1. Quantos animais você possui atualmente?  
2. Quais são as categorias e fases produtivas? (ex.: 50 bois de engorda, 20 vacas em lactação)  
3. Qual o tipo de sistema produtivo? (corte, leite, cria, recria, engorda, misto)  
4. Qual o principal objetivo no momento? (ganho de peso, produção de leite, redução de custos etc.)  
5. Onde fica sua propriedade? (estado e município)  
6. Qual a principal pastagem utilizada? (espécie e estágio de maturação)  
7. Quais volumosos você tem disponíveis? (silagem – tipo e qualidade, feno, resíduos agrícolas)  
8. Quais concentrados você possui? (milho, farelo de soja, polpa cítrica etc.)  
9. Você utiliza algum suplemento mineral atualmente? (proteinado, mineral simples, núcleo etc.)  
10. Qual o peso vivo médio de cada categoria? (em kg)  
11. Qual o ganho médio diário atual? (kg/dia)  
12. Qual o escore de condição corporal médio? (escala 1 a 9)  
13. Qual a taxa de lotação média? (UA/ha)  
14. Quando foi o último manejo sanitário ou vermifugação?  
15. Você enfrenta seca prolongada? (meses do ano)  
16. Falta volumoso em alguma época do ano? (sim/não e quando)  
17. Qual o custo máximo por cabeça/dia ou o orçamento mensal disponível para alimentação?  
18. Existe algum problema específico que deseja resolver? (baixo ganho de peso, baixa produção de leite etc.)  
19. Deseja adicionar algum insumo ou ingrediente extra na dieta? (ex.: melaço, ureia, casca de soja, caroço de algodão)  

Comece agora perguntando a primeira questão da lista.
Para a resposta final fale somente as informações básicas como a quantidade de alimento que deverá ser dada ao animal para que um produtor que não tenha tanto conhecimemento entenda perfeitamente a resposta e o ajude a ter menos disperdicío de ração.

Histórico da conversa:
{history}

Entrada do usuário:
{input}"""

# Definir prompt formatado
prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Modelo da OpenAI
llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")

# Cadeia de execução
chain = prompt | llm

# Armazenamento de histórico por sessão
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# Encadeamento com histórico
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

# --- ROTAS ---

@app.route("/")
def home():
    return "Servidor rodando! Acesse a rota /mensagem via POST."

# Rota de registro
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

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

# Rota de login
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
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[1], senha):
        session['usuario_id'] = user[0]
        return jsonify({"mensagem": "Login realizado com sucesso", "session_id": str(user[0])})
    else:
        return jsonify({"erro": "Credenciais inválidas"}), 401

# Rota para conversar com a IA e salvar histórico
@app.route("/mensagem", methods=["POST"])
def responder():
    data = request.get_json()
    pergunta_usuario = data.get("mensagem")
    session_id = data.get("session_id")

    if not pergunta_usuario:
        return jsonify({"erro": "mensagem não fornecida"}), 400

    if not session_id:
        # Se não informar session_id, não salva histórico no banco
        session_id = "usuario_padrao"

    resposta = chain_with_history.invoke(
        {"input": pergunta_usuario},
        config={"configurable": {"session_id": session_id}}
    )

    # Tenta salvar no banco se session_id for um número válido (usuário logado)
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
        pass  # se não for número válido, não salva

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

    # Retorna JSON com o histórico
    return jsonify({"historico": [
        {"pergunta": p, "resposta": r, "data": d} for p, r, d in historico
    ]})

# Rodar app
if __name__ == "__main__":
    app.run(debug=True)
