// ==============================
// CONFIGURAÇÃO DO FRONTEND
// ==============================
// Único lugar onde a URL da API é definida.
// - Padrão: mesma máquina que serve a página, porta 5000 (desenvolvimento local).
//   Usar o mesmo hostname da página (localhost x 127.0.0.1) garante que o
//   cookie de sessão seja enviado.
// - Para outro ambiente, troque este arquivo ou defina window.SVDA_CONFIG
//   antes de carregá-lo (no Docker, o nginx serve uma versão com API_BASE="/api").
window.SVDA_CONFIG = Object.assign(
  {
    API_BASE: location.protocol === 'file:'
      ? 'http://localhost:5000'
      : `${location.protocol}//${location.hostname}:5000`,
  },
  window.SVDA_CONFIG || {}
);
