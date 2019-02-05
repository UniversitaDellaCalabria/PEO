#!/bin/bash

# https://blog.khophi.co/django-management-commands-via-cron/
source /opt/django_peo.env/bin/activate && \
cd /opt/django_peo && \

export PASSWORD=$(python -c "from django_peo import settingslocal; print(settingslocal.DATABASES['default']['PASSWORD'])")
export USERNAME=$(python -c "from django_peo import settingslocal; print(settingslocal.DATABASES['default']['USER'])")
export DB=$(python -c "from django_peo import settingslocal; print(settingslocal.DATABASES['default']['NAME'])")

BACKUP_DIR="/opt/django_peo_dumps"
BACKUP_DIR_JSON=$BACKUP_DIR"/json"
BACKUP_DIR_SQL=$BACKUP_DIR"/sql"
BACKUP_DIR_MEDIA=$BACKUP_DIR"/media"
FNAME="peo.$(date +"%Y-%m-%d_%H:%M:%S")"

# JSON dump, encrypt and compress
./manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude csa --indent 2  | 7z a $BACKUP_DIR_JSON/$FNAME.json.7z -si -p$PASSWORD

# SQL dump, encrypt and compress
mysqldump -u $USERNAME --password=$PASSWORD $DB | 7z a $BACKUP_DIR_SQL/$FNAME.sql.7z -si -p$PASSWORD

# decrypt
# 7z x $BACKUP_DIR/$FNAME.7z -p$PASSWORD

# media files
rsync -avu --delete /opt/django_peo/data/media $BACKUP_DIR_MEDIA
