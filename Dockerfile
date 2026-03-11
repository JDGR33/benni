FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=UTC

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY entrypoint.sh cronjob.sh benni-cron ./

RUN chmod +x /app/entrypoint.sh /app/cronjob.sh \
    && chmod 0644 /app/benni-cron \
    && cp /app/benni-cron /etc/cron.d/benni-cron

ENTRYPOINT ["/app/entrypoint.sh"]
