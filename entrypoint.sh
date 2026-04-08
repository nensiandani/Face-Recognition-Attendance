#!/bin/sh

# 1. Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --no-input

# 2. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# 3. Setup Google OAuth credentials in DB (fixes Error 400: missing client_id)
echo "Setting up Google OAuth..."
python manage.py setup_google_auth

# 4. Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn visionai.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 2 --timeout 120