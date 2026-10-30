# Deploying SVDA

[Leia em português](deploy.pt-BR.md)

SVDA is one Docker image: the Flask API plus, with `SERVE_FRONTEND=true`, the static frontend. One container = one URL, same origin (no CORS). The SQLite database lives in `/data`, so the host **must provide a persistent disk/volume** mounted there. Hosts without persistent disks (Vercel, Netlify, free tiers that sleep and wipe the disk) will lose sign-ups and history.

> The OpenAI API is paid. A public demo lets anyone create an account and spend **your** credit, so use the protections below.

## 1. Protect your credit

| Setting | What it does |
| --- | --- |
| `INVITE_CODE` | Sign-up requires this code. Share it only with people you want to try the demo. |
| `DAILY_MESSAGE_LIMIT` | Hard cap of messages per day (UTC) across all users. When reached, the API answers 429 without calling OpenAI. Example: `200`. |
| OpenAI project limits | In the OpenAI dashboard, use a dedicated key for the demo with a **monthly spend limit**. Never reuse a key that was ever pasted in a chat, issue or commit. |

The per-user rate limits (`RATE_LIMIT_*`) stay active. Keep a single server process: the default limiter is in memory.

## 2. Environment variables

Set these in the host's dashboard or secret store (never in the repository):

```text
APP_ENV=production
SECRET_KEY=<python -c "import secrets; print(secrets.token_hex(32))">
OPENAI_API_KEY=<your key>
SERVE_FRONTEND=true
DATABASE_PATH=/data/banco.db
SESSION_COOKIE_SECURE=true
PROXY_FIX_X_FOR=1
LOG_FORMAT=json
INVITE_CODE=<a code you choose>
DAILY_MESSAGE_LIMIT=200
```

`PROXY_FIX_X_FOR=1` makes the rate limiter see the real client IP behind the host's proxy (use the number of proxies in front of the app). Health check path: `/healthz`. The container listens on port `5000`.

## 3. Example: Fly.io

```bash
fly launch --no-deploy            # detects the Dockerfile, creates fly.toml
fly volumes create svda_data --size 1
fly secrets set SECRET_KEY=... OPENAI_API_KEY=... INVITE_CODE=...
```

Edit `fly.toml`:

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

Then `fly deploy`. Keep a single machine (`fly scale count 1`) because the volume belongs to one machine.

## 4. Other hosts

**Render:** create a *Web Service* from the repository (Docker runtime), add a *Disk* mounted at `/data`, and set the environment variables above (health check path `/healthz`). Persistent disks need a paid instance.

**Railway:** deploy the repository with the Dockerfile, add a *Volume* mounted at `/data`, set the variables above.

The container starts as root only to fix the ownership of the mounted disk, then drops to an unprivileged user before starting the app.

## 5. After deploying

1. Open the URL, sign up with the invite code, log in and ask a question.
2. Check the logs: a line like `LLM answer truncated by max_tokens` means answers are being cut; raise `LLM_MAX_TOKENS` if it is frequent.
3. Back up `/data/banco.db` (it holds users and conversations).
