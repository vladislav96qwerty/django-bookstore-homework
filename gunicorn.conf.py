"""
gunicorn.conf.py — конфігурація Gunicorn для production.
Використовується: gunicorn -c gunicorn.conf.py bookstore.wsgi:application
"""

import os
import multiprocessing

# ── Binding ───────────────────────────────────────────────────────────────────
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# ── Workers ───────────────────────────────────────────────────────────────────
# Стандартна формула: 2 * CPU + 1
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
threads = 2
worker_connections = 1000

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout = 120
keepalive = 5
graceful_timeout = 30

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)ss'

# ── Process naming ────────────────────────────────────────────────────────────
proc_name = "bookstore"

# ── Security ──────────────────────────────────────────────────────────────────
limit_request_line = 4096
limit_request_fields = 100
