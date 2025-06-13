import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify

from langchain_openai import ChatOpenAI 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar Flask
app = Flask(__name__)

# Template do prompt
template = """Você vai auxiliar no manejo de ração para gados em geral para uma melhor alimentação custo benefício ao produtor.
A primeira coisa que deve fazer é perguntar ao produtor sobre a quantidade de cabeças de gado possue em sua fazenda e seu orçamento.

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

# Endpoint que responde ao frontend
from flask import Flask, request, jsonify
import json
from flask_cors import CORS



app = Flask(__name__)
CORS(app)  # libera todas as origens
app.config['JSON_AS_ASCII'] = False

@app.route("/")
def home():
    return "Servidor rodando! Acesse a rota /mensagem via POST."

@app.route("/mensagem", methods=["POST"])
def responder():
    data = request.get_json()
    pergunta_usuario = data.get("mensagem")
    session_id = data.get("session_id", "usuario_padrao")

    if not pergunta_usuario:
        return jsonify({"erro": "mensagem não fornecida"}), 400

    resposta = chain_with_history.invoke(
        {"input": pergunta_usuario},
        config={"configurable": {"session_id": session_id}}
    )

    return jsonify({"resposta": resposta.content})

if __name__ == "__main__":
    app.run(debug=True)



