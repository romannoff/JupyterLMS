#!/usr/bin/env bash
set -e

echo "=== Applying database migrations ==="
python manage.py makemigrations
python manage.py migrate

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && \
   [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && \
   [ -n "$DJANGO_SUPERUSER_EMAIL" ]; then

  echo "=== Checking if superuser $DJANGO_SUPERUSER_USERNAME exists ==="
  python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
username = "$DJANGO_SUPERUSER_USERNAME"
email = "$DJANGO_SUPERUSER_EMAIL"
password = "$DJANGO_SUPERUSER_PASSWORD"

if not User.objects.filter(username=username).exists():
    print("Creating superuser $DJANGO_SUPERUSER_USERNAME")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print("Superuser $DJANGO_SUPERUSER_USERNAME already exists, skipping creation")
EOF

fi

echo "=== Starting Django server on 0.0.0.0:8008 ==="
exec python manage.py runserver 0.0.0.0:8008