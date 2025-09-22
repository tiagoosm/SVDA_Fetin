const API_BASE = 'http://127.0.0.1:5000';
const input = document.querySelector('.input-text');
const sendBtn = document.querySelector('.send-btn');
const chatContainer = document.querySelector('.chat-container');
const messagesDiv = document.querySelector('.messages');

function addMessage(text, sender) {
  const messageWrapper = document.createElement('div');
  messageWrapper.classList.add('message-wrapper');

  const p = document.createElement('p');
  p.innerHTML = marked.parse(text);
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
// função para mostrar a mensagem digitando.
function addMessageTyping(text, sender, velocidade = 3) {
  const messageWrapper = document.createElement('div');
  messageWrapper.classList.add('message-wrapper');

  const p = document.createElement('p');
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

  // texto parcial que vai crescendo
  let parcial = "";
  let i = 0;

  function escrever() {
    if (i < text.length) {
      parcial += text.charAt(i);
      // renderiza markdown do texto parcial
      p.innerHTML = marked.parse(parcial);
      i++;
      setTimeout(escrever, velocidade);
    }
  }
  escrever();
}



sendBtn.addEventListener('click', async () => {
  const mensagem = input.value.trim();
  if (!mensagem) return;

  addMessage(mensagem, 'Você');
  input.value = "";

  const sessionId = localStorage.getItem('session_id') || null;
  const conversaId = localStorage.getItem('conversa_id') || null;

  try {
    const response = await fetch(`${API_BASE}/mensagem`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mensagem, session_id: sessionId, conversa_id: conversaId })
    });

    if (!response.ok) {
      addMessage("Erro ao receber resposta do servidor.", "Sistema");
      return;
    }

    const data = await response.json();
    addMessageTyping(data.resposta, 'SVDA',);

    if (data.conversa_id) {
      localStorage.setItem('conversa_id', data.conversa_id);
    }
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

window.addEventListener('DOMContentLoaded', async () => {
  const sessionId = localStorage.getItem('session_id') || null;
  const conversaId = localStorage.getItem('conversa_id') || null;
  if (conversaId) {
    try {
      const url = `${API_BASE}/historico?conversa_id=${encodeURIComponent(conversaId)}${sessionId ? '&session_id=' + encodeURIComponent(sessionId) : ''}`;
      const resp = await fetch(url);
      const data = await resp.json();

      if (resp.ok && data.historico) {
        // mostramos do mais recente para o mais antigo (inverter para exibir cronologicamente)
        data.historico.forEach(msg => {
          addMessage(msg.pergunta, 'Você');
          addMessage(msg.resposta, 'SVDA');
        });
        return;
      }
    } catch (err) {
      console.error("Erro ao carregar histórico", err);
    }
  }

  // mensagem inicial padrão
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
  localStorage.removeItem('conversa_id'); 
  window.location.href = 'login.html';  
}

