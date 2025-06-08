import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI 
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
#Importacoes das bibliotecas do langchain

template = """Você vai auxiliar no manejo de ração para gados em geral para uma melhor alimentação custo benefício ao produtor.
A primeira coisa que deve fazer é perguntar ao produtor sobre a quantidade de cabeças de gado possue em sua fazenda e seu orçamento.

Histórico da conversa:
{history}

Entrada do usuário:
{input}"""
#Aqui é onde criamos o prompit para IA e onde ela vai receber a entrada de dados do usuario

prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])
#Variavel prompit para inicar o chatprompttamplate, ou seja, o jeito que ele vai se comportar

llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
#inicar o modelo de linguagem(temperature = criatividade da IA na resposta e o model é o chat que estamos usando)

chain = prompt | llm

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]
#Criacao do historico

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)
#Linkagem com historico

def iniciar_SVDA():
    #Criacao da assistente
    print("Bem-vindo ao SVDA! Digite 'sair' para encerrar.\n")
    while True:
        pergunta_usuario = input("Você: ")
        if pergunta_usuario.lower() in ["sair", "exit"]:
            print("SVDA: Obrigado!")
            break

        resposta = chain_with_history.invoke(
            {'input': pergunta_usuario},
            config={'configurable': {'session_id': 'user123'}}
        )
        #Executar o assistente

        print("SVDA:", resposta.content)
        #Resposta da IA sobre a pergunta do usuario

if __name__ == "__main__":
    iniciar_SVDA()
    