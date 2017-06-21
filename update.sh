#! /bin/sh

set -e

echo "----- Updating Python Dependencies -----"
python -m pip install -r requirements-dev.txt

echo "----- Migrating Database -----"
python manage.py migrate --noinput
