// ==============================
// CLIENTE DA API (compartilhado por todas as páginas)
// ==============================
const API_BASE = window.SVDA_CONFIG.API_BASE;

// Faz uma requisição à API enviando o cookie de sessão.
// Em 401 (sessão ausente/expirada) volta para a tela de login,
// exceto quando redirectOn401 = false (telas de login e cadastro).
async function apiFetch(path, { method = 'GET', body, redirectOn401 = true } = {}) {
  const options = { method, credentials: 'include', headers: {} };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  const resp = await fetch(`${API_BASE}${path}`, options);
  if (resp.status === 401 && redirectOn401) {
    window.location.href = 'index.html';
    throw new Error('Não autenticado');
  }
  const data = await resp.json().catch(() => ({}));
  return { ok: resp.ok, status: resp.status, data };
}

// Encerra a sessão no servidor e volta para o login
async function logout() {
  try {
    await apiFetch('/logout', { method: 'POST', redirectOn401: false });
  } catch (err) {
    console.error(err);
  }
  localStorage.removeItem('conversa_id');
  window.location.href = 'index.html';
}
