#!/usr/bin/env bash

set -o errexit
set -o nounset
set -o pipefail

python manage.py migrate --noinput
gunicorn Chat_site.wsgi:application

