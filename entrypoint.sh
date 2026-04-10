#!/bin/sh

# 0. Wait for DB to be reachable (max 30 seconds)
echo "Waiting for database connection..."
MAX_RETRIES=10
RETRY=0

until python -c "
import os, psycopg2
from urllib.parse import urlparse
url = urlparse(os.environ.get('DATABASE_URL', ''))
conn = psycopg2.connect(
    dbname=url.path[1:],
    user=url.username,
    password=url.password,
    host=url.hostname,
    port=url.port or 5432,
    sslmode='require',
    connect_timeout=5
)
conn.close()
print('DB connected!')
" 2>/dev/null; do
  RETRY=$((RETRY+1))
  if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "❌ Could not connect to database after $MAX_RETRIES attempts. Check DATABASE_URL and network/DNS."
    exit 1
  fi
  echo "⏳ DB not ready, retrying ($RETRY/$MAX_RETRIES)..."
  sleep 3
done

echo "✅ Database is reachable!"

# 1. Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --no-input

# 2. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# 3. Setup Google OAuth credentials in DB
echo "Setting up Google OAuth..."
python manage.py setup_google_auth

# 4. Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn visionai.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 2 --timeout 120