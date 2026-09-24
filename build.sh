#!/bin/bash
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --settings=tours_travels.settings_prod

echo "Applying migrations..."
python manage.py migrate --noinput --settings=tours_travels.settings_prod

echo "Creating cache table if needed..."
python manage.py createcachetable --settings=tours_travels.settings_prod || true

echo "Build complete."
