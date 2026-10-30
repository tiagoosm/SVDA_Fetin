# SVDA backend: Flask API served by gunicorn
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY wsgi.py .

# The app runs as an unprivileged user (see entrypoint.sh); the SQLite database
# lives in the /data volume.
RUN useradd --create-home --uid 10001 svda \
    && mkdir /data && chown svda /data
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV DATABASE_PATH=/data/svda.db
VOLUME /data

EXPOSE 5000

# One worker + threads: the default in-memory rate limiter is per process, so a
# single worker keeps the limits exact. Use Redis (RATELIMIT_STORAGE_URI) before
# raising the number of workers.
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "60", "wsgi:app"]
