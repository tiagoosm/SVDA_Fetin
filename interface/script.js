const input = document.querySelector('.input-text');
const sendBtn = document.querySelector('.send-btn');
const chatContainer = document.querySelector('.chat-container');

const messagesDiv = document.createElement('div');
messagesDiv.classList.add('messages');
chatContainer.appendChild(messagesDiv);

function addMessage(text, sender) {
  const messageWrapper = document.createElement('div');
  messageWrapper.classList.add('message-wrapper');

  const p = document.createElement('p');
  p.textContent = text;
  p.classList.add('message');

  if (sender === 'Você') {
    messageWrapper.classList.add('sent');
    p.classList.add('message-sent');
  } 
  else if (sender === 'IA' || sender === 'SVDA') {
    messageWrapper.classList.add('received');
    p.classList.add('message-received');
  } 
  else {
    messageWrapper.classList.add('system');
    p.classList.add('message-system');
  }

  messageWrapper.appendChild(p);
  messagesDiv.prepend(messageWrapper);
}

sendBtn.addEventListener('click', async () => {
  const mensagem = input.value.trim();
  if (!mensagem) return;

  addMessage(mensagem, 'Você');
  input.value = "";

  // pega o session_id salvo após login
  const sessionId = localStorage.getItem('session_id') || null;

  try {
    const response = await fetch('http://127.0.0.1:5000/mensagem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // não precisa credenciais nesta rota; usa session_id no body
      body: JSON.stringify({ mensagem, session_id: sessionId })
    });

    if (!response.ok) {
      addMessage("Erro ao receber resposta do servidor.", "Sistema");
      return;
    }

    const data = await response.json();
    addMessage(data.resposta, 'SVDA');
  } catch (error) {
    addMessage("Erro ao conectar com o servidor.", 'Sistema');
    console.error(error);
  }
});

input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendBtn.click();
  }
});

document.querySelector('.back-btn')?.addEventListener('click', function() {
  // ao voltar, opcionalmente sair
  window.location.href = 'login.html';
});

window.addEventListener('DOMContentLoaded', () => {
  addMessage(
    "Olá! Nós somos os Serviços de Dados Alimentícios, SVDA. Estamos aqui para ajudar você com: - Formular dietas equilibradas para o seu gado. - Reduzir custos e melhorar o desempenho. - Dar orientações de manejo em época de estiagem. - Apoiar na saúde e tratamento do gado. - Responder dúvidas do dia a dia da fazenda. Como podemos ajudar você hoje?",
    'SVDA'
  );
});
