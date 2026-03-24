#!/bin/sh

# 1. Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --no-input

# 2. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# 3. Setup Site only
echo "Setting up Site..."
python manage.py shell << 'EOF'
import os
from django.contrib.sites.models import Site

domain = os.environ.get('SITE_DOMAIN', 'localhost:8000')
Site.objects.update_or_create(
    id=1,
    defaults={'domain': domain, 'name': domain}
)
print(f"Site set to: {domain}")
EOF

# 4. Start Gunicorn server
echo "Starting Gunicorn server..."
exec gunicorn visionai.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 2 --timeout 120