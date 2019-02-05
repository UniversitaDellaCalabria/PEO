#!/bin/bash

# https://blog.khophi.co/django-management-commands-via-cron/
# source /opt/django_peo.env/bin/activate && \
# cd /opt/django_peo && \

export PASSWORD=$(python -c "from django_peo import settingslocal; print(settingslocal.DATABASES['default']['PASSWORD'])")
export USERNAME=$(python -c "from django_peo import settingslocal; print(settingslocal.DATABASES['default']['USER'])")
export DB=$(python -c "from django_peo import settingslocal; print(settingslocal.DATABASES['default']['NAME'])")

# BACKUP_DIR="/opt/django_peo_dumps"
BACKUP_DIR="/tmp"
BACKUP_DIR_JSON=$BACKUP_DIR"/json"
BACKUP_DIR_SQL=$BACKUP_DIR"/sql"
FNAME="peo.$(date +"%Y-%m-%d_%H:%M:%S")"
IV=6475

./manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude csa --indent 2  | \
tar -czf - | \
openssl enc -e -aes-256 -k $PASSWORD -iv $IV -base64 -out $BACKUP_DIR/$FNAME.json.gz.aes

# decrypt
# openssl enc -aes-256 -d -k $PASSWORD -iv $IV -base64 -in $BACKUP_DIR/$FNAME.json.gz.aes | gzip -d

# SQL dump, encrypt and compress
mysqldump -u $USERNAME --password=$PASSWORD $DB | \
gzip | \
openssl enc -aes-256-cbc -e -k $PASSWORD -iv $IV -base64 > $BACKUP_DIR_SQL/$FNAME.sql.gz.aes
