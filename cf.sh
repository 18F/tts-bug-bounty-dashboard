#!/bin/bash

set -e

if [ $CF_INSTANCE_INDEX = "0" ]; then
    echo "----- Migrating Database -----"
    python manage.py migrate --noinput
fi
echo "------ Starting APP ------"
gunicorn bugbounty.wsgi:application
