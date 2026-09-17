#!/bin/bash

# Build the project
# Build the project
set -o errexit  # exit on error
echo "Building the project JDA..."




pip install -r requirements.txt

python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput
python manage.py createsu 