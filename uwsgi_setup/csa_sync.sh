#!/bin/bash

# https://blog.khophi.co/django-management-commands-via-cron/
source /opt/django_peo.env/bin/activate && cd /opt/django_peo && ./manage.py csa_sync
