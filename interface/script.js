const input = document.querySelector('.input-text');
const sendBtn = document.querySelector('.send-btn');
const chatContainer = document.querySelector('.chat-container');
const messagesDiv = document.querySelector('.messages');

function addMessage(text, sender) {
  const messageWrapper = document.createElement('div');
  messageWrapper.classList.add('message-wrapper');

  const p = document.createElement('p');
  p.innerHTML = marked.parse(text); // Markdown -> HTML
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

  const sessionId = localStorage.getItem('session_id') || null;

  try {
    const response = await fetch('http://127.0.0.1:5000/mensagem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

document.querySelector('.back-btn')?.addEventListener('click', () => {
  window.location.href = 'conversas.html';
});

window.addEventListener('DOMContentLoaded', () => {
  addMessage(
    `👋 Olá, seja bem-vindo ao Serviço de Dados Alimentícios – SVDA!

Aqui o seu rebanho vem em primeiro lugar. Nosso objetivo é deixar a sua vida no campo mais simples e produtiva, oferecendo apoio em tudo o que você precisa:

🐂 Formular dietas equilibradas e econômicas para o seu gado

💰 Reduzir custos e aumentar o desempenho do rebanho

🌱 Orientar no manejo durante a seca ou nas águas

💉 Apoiar na saúde e vacinação do gado

📌 Responder dúvidas práticas do dia a dia da fazenda

✨ Estamos prontos para caminhar junto com você — do pequeno ao grande produtor.

👉 Como podemos ajudar você hoje?`,
    'SVDA'
  );
});

function logout() {
  localStorage.removeItem('session_id'); 
  window.location.href = 'login.html';  
}
