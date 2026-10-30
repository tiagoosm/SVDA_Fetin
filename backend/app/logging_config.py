"""Logging estruturado (JSON ou texto) e log de requisições."""

import json
import logging
import time
import uuid

from flask import g, request, session


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Campos extras passados via logger.info(..., extra={...})
        for key in ("request_id", "method", "path", "status", "duration_ms", "user_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level="INFO", fmt="text"):
    handler = logging.StreamHandler()
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())


def register_request_logging(app):
    logger = logging.getLogger("svda.request")

    @app.before_request
    def start_timer():
        g.request_start = time.perf_counter()
        g.request_id = request.headers.get("X-Request-Id", uuid.uuid4().hex[:12])[:64]

    @app.after_request
    def log_request(response):
        if request.path != "/health":  # ignore the health check
            logger.info(
                "%s %s -> %s",
                request.method,
                request.path,
                response.status_code,
                extra={
                    "request_id": g.get("request_id"),
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": round((time.perf_counter() - g.get("request_start", time.perf_counter())) * 1000, 1),
                    # Só o ID do usuário; nunca o conteúdo das mensagens
                    "user_id": session.get("user_id"),
                },
            )
        response.headers["X-Request-Id"] = g.get("request_id", "")
        return response
