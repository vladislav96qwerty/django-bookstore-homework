FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "Django>=5,<7" "psycopg[binary]>=3.1"

COPY . /app

RUN chmod +x /app/docker-entrypoint.sh || true

