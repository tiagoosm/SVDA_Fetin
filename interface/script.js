// ==============================
// CONFIGURAÇÃO INICIAL
// ==============================
// API_BASE, apiFetch e logout vêm de config.js e api.js
const input = document.querySelector('.input-text');       // Campo de entrada de texto
const sendBtn = document.querySelector('.send-btn');       // Botão de enviar
const messagesDiv = document.querySelector('.messages');   // Div que vai conter as mensagens

const TYPING_CHARS_PER_TICK = 4; // Letras reveladas a cada passo da digitação
const TYPING_TICK_MS = 15;       // Intervalo entre passos (ms)

const WELCOME_MESSAGE = `👋 Olá, seja bem-vindo ao SVDA!

Aqui o seu rebanho vem em primeiro lugar. Nosso objetivo é deixar a sua vida no campo mais simples e produtiva, oferecendo apoio em tudo o que você precisa:

🐂 Formular dietas equilibradas e econômicas para o seu gado

💰 Reduzir custos e aumentar o desempenho do rebanho

🌱 Orientar no manejo durante a seca ou nas águas

💉 Apoiar na saúde e vacinação do gado

📌 Responder dúvidas práticas do dia a dia da fazenda

✨ Estamos prontos para caminhar junto com você — do pequeno ao grande produtor.

👉 Como podemos ajudar você hoje?`;

// ==============================
// FUNÇÃO: converter markdown em HTML seguro
// ==============================
// Texto do usuário e da IA nunca vai para o DOM sem passar pelo DOMPurify (evita XSS)
function renderMarkdown(text) {
  return DOMPurify.sanitize(marked.parse(text));
}

// ==============================
// FUNÇÃO: efeito de digitação
// ==============================
// O markdown é convertido UMA vez; depois os nós de texto já renderizados
// são revelados aos poucos, sem reprocessar o markdown a cada letra.
function typeInto(element) {
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
  const nodes = [];
  while (walker.nextNode()) {
    nodes.push({ node: walker.currentNode, full: walker.currentNode.textContent });
    walker.currentNode.textContent = '';
  }

  let index = 0;
  let shown = 0;
  function step() {
    let budget = TYPING_CHARS_PER_TICK;
    while (budget > 0 && index < nodes.length) {
      const { node, full } = nodes[index];
      const take = Math.min(budget, full.length - shown);
      shown += take;
      budget -= take;
      node.textContent = full.slice(0, shown);
      if (shown >= full.length) {
        index++;
        shown = 0;
      }
    }
    if (index < nodes.length) setTimeout(step, TYPING_TICK_MS);
  }
  step();
}

// ==============================
// FUNÇÃO: adicionar mensagem no chat
// ==============================
// sender: 'Você' (usuário), 'SVDA' (assistente) ou qualquer outro valor (sistema)
function addMessage(text, sender, { typing = false } = {}) {
  const messageWrapper = document.createElement('div'); // Cria container da mensagem
  messageWrapper.classList.add('message-wrapper');

  const p = document.createElement('p');
  p.classList.add('message');

  // Define estilo conforme remetente
  if (sender === 'Você') {
    messageWrapper.classList.add('sent');
    p.classList.add('message-sent');
  } else if (sender === 'SVDA') {
    messageWrapper.classList.add('received');
    p.classList.add('message-received');
  } else {
    messageWrapper.classList.add('system');
    p.classList.add('message-system');
  }

  p.innerHTML = renderMarkdown(text); // Renderiza markdown sanitizado
  messageWrapper.appendChild(p);
  messagesDiv.prepend(messageWrapper); // Adiciona mensagem na tela (no topo)

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (typing && !reduceMotion) typeInto(p);
}

// ==============================
// EVENTO: clique no botão de enviar mensagem
// ==============================
sendBtn.addEventListener('click', async () => {
  const mensagem = input.value.trim(); // Pega mensagem digitada
  if (!mensagem) return;               // Se vazio, não faz nada

  addMessage(mensagem, 'Você'); // Mostra mensagem no chat
  input.value = "";             // Limpa campo de texto
  sendBtn.disabled = true;      // Evita envios duplicados enquanto aguarda

  // conversa_id fica no localStorage; o usuário é identificado pelo cookie de sessão
  const conversaId = localStorage.getItem('conversa_id') || null;

  try {
    const { ok, data } = await apiFetch('/mensagem', {
      method: 'POST',
      body: { mensagem, conversa_id: conversaId },
    });

    // Caso a resposta não seja válida, mostra a mensagem de erro da API
    if (!ok) {
      addMessage(data.erro || "Erro ao receber resposta do servidor.", "Sistema");
      return;
    }

    // Mostra resposta da IA com efeito de digitação
    addMessage(data.resposta, 'SVDA', { typing: true });

    // Atualiza conversa_id no localStorage (mantém continuidade da conversa)
    if (data.conversa_id) {
      localStorage.setItem('conversa_id', data.conversa_id);
    }
  } catch (error) {
    addMessage("Erro ao conectar com o servidor.", 'Sistema');
    console.error(error);
  } finally {
    sendBtn.disabled = false;
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
// EVENTO: carregar histórico da conversa ao abrir a página
// ==============================
window.addEventListener('DOMContentLoaded', async () => {
  const conversaId = localStorage.getItem('conversa_id') || null;

  try {
    // Se já existe conversa, busca histórico no backend
    if (conversaId) {
      const { ok, data } = await apiFetch(`/historico?conversa_id=${encodeURIComponent(conversaId)}`);
      if (ok && data.historico && data.historico.length > 0) {
        // Mostra as mensagens (pergunta e resposta)
        data.historico.forEach(msg => {
          addMessage(msg.pergunta, 'Você');
          addMessage(msg.resposta, 'SVDA');
        });
        return;
      }
    } else {
      // Nova conversa: só confirma que o usuário está logado (redireciona se não estiver)
      await apiFetch('/me');
    }
  } catch (err) {
    console.error("Erro ao carregar histórico", err);
    return;
  }

  // Caso não haja histórico, mostra mensagem inicial padrão de boas-vindas
  addMessage(WELCOME_MESSAGE, 'SVDA');
});
