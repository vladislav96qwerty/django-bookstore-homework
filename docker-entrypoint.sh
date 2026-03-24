#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "import os, socket; s=socket.socket(); s.settimeout(2); s.connect((os.getenv('DB_HOST', 'db'), int(os.getenv('DB_PORT', '5432')))); s.close()" 2>/dev/null
do
  sleep 1
done
echo "PostgreSQL is available."

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000

