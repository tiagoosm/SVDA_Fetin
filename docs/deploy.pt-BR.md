# Publicando o SVDA

[Read in English](deploy.md)

O SVDA é uma única imagem Docker: a API Flask e, com `SERVE_FRONTEND=true`, também o frontend estático. Um contêiner = uma URL, mesma origem (sem CORS). O SQLite fica em `/data`, então o host **precisa oferecer disco/volume persistente** montado ali. Hosts sem disco persistente (Vercel, Netlify, planos gratuitos que dormem e apagam o disco) perdem cadastros e histórico.

> A API da OpenAI é paga. Uma demo pública deixa qualquer pessoa criar conta e gastar o **seu** crédito, então use as proteções abaixo.

## 1. Proteja o seu crédito

| Configuração | O que faz |
| --- | --- |
| `INVITE_CODE` | O cadastro exige esse código. Compartilhe só com quem você quer que teste a demo. |
| `DAILY_MESSAGE_LIMIT` | Teto de mensagens por dia (UTC) somando todos os usuários. Ao atingir, a API responde 429 sem chamar a OpenAI. Exemplo: `200`. |
| Limites no painel da OpenAI | Use uma chave exclusiva da demo, com **limite de gasto mensal**. Nunca reutilize uma chave que já foi colada em chat, issue ou commit. |

Os limites por usuário (`RATE_LIMIT_*`) continuam ativos. Mantenha um único processo do servidor: o limitador padrão fica em memória.

## 2. Variáveis de ambiente

Defina no painel ou no cofre de segredos do host (nunca no repositório):

```text
APP_ENV=production
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">
OPENAI_API_KEY=<sua chave>
SERVE_FRONTEND=true
DATABASE_PATH=/data/banco.db
SESSION_COOKIE_SECURE=true
PROXY_FIX_X_FOR=1
LOG_FORMAT=json
INVITE_CODE=<um código que você escolhe>
DAILY_MESSAGE_LIMIT=200
```

`PROXY_FIX_X_FOR=1` faz o limitador enxergar o IP real do cliente atrás do proxy do host (use o número de proxies na frente do app). Caminho do health check: `/healthz`. O contêiner escuta na porta `5000`.

## 3. Exemplo: Fly.io

```bash
fly launch --no-deploy            # detecta o Dockerfile e cria o fly.toml
fly volumes create svda_data --size 1
fly secrets set SECRET_KEY=... OPENAI_API_KEY=... INVITE_CODE=...
```

Edite o `fly.toml`:

```toml
[env]
  APP_ENV = "production"
  SERVE_FRONTEND = "true"
  DATABASE_PATH = "/data/banco.db"
  SESSION_COOKIE_SECURE = "true"
  PROXY_FIX_X_FOR = "1"
  LOG_FORMAT = "json"
  DAILY_MESSAGE_LIMIT = "200"

[mounts]
  source = "svda_data"
  destination = "/data"

[http_service]
  internal_port = 5000
  force_https = true
  [[http_service.checks]]
    path = "/healthz"
    interval = "30s"
    timeout = "5s"
```

Depois, `fly deploy`. Mantenha uma única máquina (`fly scale count 1`), porque o volume pertence a uma máquina só.

## 4. Outros hosts

**Render:** crie um *Web Service* a partir do repositório (runtime Docker), adicione um *Disk* montado em `/data` e defina as variáveis acima (health check em `/healthz`). Disco persistente exige instância paga.

**Railway:** faça o deploy do repositório com o Dockerfile, adicione um *Volume* montado em `/data` e defina as variáveis acima.

O contêiner inicia como root apenas para ajustar o dono do disco montado e, em seguida, passa a um usuário sem privilégios antes de iniciar o app.

## 5. Depois de publicar

1. Abra a URL, cadastre-se com o código de convite, faça login e pergunte algo.
2. Confira os logs: uma linha como `LLM answer truncated by max_tokens` indica respostas cortadas; aumente `LLM_MAX_TOKENS` se for frequente.
3. Faça backup de `/data/banco.db` (guarda usuários e conversas).
