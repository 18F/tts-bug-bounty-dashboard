#! /bin/sh

set -e

echo "----- Updating Python Dependencies -----"
python -m pip install -r requirements.txt

echo "----- Migrating Database -----"
python manage.py migrate --noinput
