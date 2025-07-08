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

  try {
    const response = await fetch('http://127.0.0.1:5000/mensagem', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mensagem, session_id: "usuario_teste" })
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