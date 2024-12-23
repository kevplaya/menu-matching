#!/bin/bash
set -e

echo "Waiting for MySQL to be ready..."
while ! mysqladmin ping -h"db" --silent; do
    sleep 1
done

echo "Running migrations..."
python manage.py migrate

echo "Ensuring standard menus exist..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from scripts.create_sample_data import create_standard_menus
create_standard_menus()
"

echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print('Superuser created.')
else:
    print('Superuser already exists.')
EOF

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000
