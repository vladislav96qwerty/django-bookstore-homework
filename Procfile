web: gunicorn bookstore.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120 --access-logfile - --error-logfile -
worker: celery -A bookstore worker --loglevel=info --concurrency=4
beat: celery -A bookstore beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
