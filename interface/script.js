// ==============================
// CONFIGURAÇÃO INICIAL
// ==============================
const API_BASE = 'http://127.0.0.1:5000'; // URL base da API Flask (backend)
const input = document.querySelector('.input-text');       // Campo de entrada de texto
const sendBtn = document.querySelector('.send-btn');       // Botão de enviar
const chatContainer = document.querySelector('.chat-container'); // Container do chat
const messagesDiv = document.querySelector('.messages');   // Div que vai conter as mensagens

// ==============================
// FUNÇÃO: adicionar mensagem no chat
// ==============================
function addMessage(text, sender) {
  const messageWrapper = document.createElement('div'); // Cria container da mensagem
  messageWrapper.classList.add('message-wrapper');

  const p = document.createElement('p'); // Cria parágrafo com o texto
  p.innerHTML = marked.parse(text);      // Usa "marked" para renderizar markdown
  p.classList.add('message');

  // Define estilo conforme remetente
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

  // Adiciona mensagem na tela (no topo)
  messageWrapper.appendChild(p);
  messagesDiv.prepend(messageWrapper);
}

// ==============================
// FUNÇÃO: mostrar mensagem "digitando" letra por letra
// ==============================
function addMessageTyping(text, sender, velocidade = 3) {
  const messageWrapper = document.createElement('div');
  messageWrapper.classList.add('message-wrapper');

  const p = document.createElement('p');
  p.classList.add('message');

  // Define estilo conforme remetente
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

  // Texto parcial vai crescendo como se fosse digitado
  let parcial = "";
  let i = 0;

  function escrever() {
    if (i < text.length) {
      parcial += text.charAt(i);              // Adiciona letra por letra
      p.innerHTML = marked.parse(parcial);    // Renderiza o markdown parcial
      i++;
      setTimeout(escrever, velocidade);       // Controla velocidade da digitação
    }
  }
  escrever();
}

// ==============================
// EVENTO: clique no botão de enviar mensagem
// ==============================
sendBtn.addEventListener('click', async () => {
  const mensagem = input.value.trim(); // Pega mensagem digitada
  if (!mensagem) return;               // Se vazio, não faz nada

  addMessage(mensagem, 'Você'); // Mostra mensagem no chat
  input.value = "";             // Limpa campo de texto

  // Recupera session_id e conversa_id do localStorage
  const sessionId = localStorage.getItem('session_id') || null;
  const conversaId = localStorage.getItem('conversa_id') || null;

  try {
    // Envia mensagem para o backend Flask
    const response = await fetch(`${API_BASE}/mensagem`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mensagem, session_id: sessionId, conversa_id: conversaId })
    });

    // Caso a resposta não seja válida
    if (!response.ok) {
      addMessage("Erro ao receber resposta do servidor.", "Sistema");
      return;
    }

    // Resposta da API (json)
    const data = await response.json();

    // Mostra resposta da IA com efeito de digitação
    addMessageTyping(data.resposta, 'SVDA');

    // Atualiza conversa_id no localStorage (mantém continuidade da conversa)
    if (data.conversa_id) {
      localStorage.setItem('conversa_id', data.conversa_id);
    }
  } catch (error) {
    addMessage("Erro ao conectar com o servidor.", 'Sistema');
    console.error(error);
  }
});

// ==============================
// EVENTO: enviar com tecla Enter
// ==============================
input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendBtn.click(); // Simula clique no botão de enviar
  }
});

// ==============================
// EVENTO: voltar para a lista de conversas
// ==============================
document.querySelector('.back-btn')?.addEventListener('click', () => {
  window.location.href = 'conversas.html';
});

// ==============================
// EVENTO: carregar histórico da conversa ao abrir a página
// ==============================
window.addEventListener('DOMContentLoaded', async () => {
  const sessionId = localStorage.getItem('session_id') || null;
  const conversaId = localStorage.getItem('conversa_id') || null;

  // Se já existe conversa, busca histórico no backend
  if (conversaId) {
    try {
      const url = `${API_BASE}/historico?conversa_id=${encodeURIComponent(conversaId)}${sessionId ? '&session_id=' + encodeURIComponent(sessionId) : ''}`;
      const resp = await fetch(url);
      const data = await resp.json();

      if (resp.ok && data.historico) {
        // Mostra as mensagens (pergunta e resposta)
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

  // Caso não haja histórico, mostra mensagem inicial padrão de boas-vindas
  addMessage(
    `👋 Olá, seja bem-vindo ao Serviço de Dados Alimentícios Bovinos – SVDAD!

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

// ==============================
// FUNÇÃO: logout (sair)
// ==============================
function logout() {
  localStorage.removeItem('session_id');  // Remove ID da sessão
  localStorage.removeItem('conversa_id'); // Remove ID da conversa
  window.location.href = 'index.html';    // Redireciona para tela de login
}
