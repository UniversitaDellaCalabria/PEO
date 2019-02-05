#!/bin/bash

BACKUP_DIR="/opt/django_peo_dumps"
BACKUP_DIR_JSON=$BACKUP_DIR"/json"
BACKUP_DIR_SQL=$BACKUP_DIR"/sql"
FNAME="peo.$(date +"%Y-%m-%d_%H:%M:%S")" 

# https://blog.khophi.co/django-management-commands-via-cron/
# ./manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude csa --indent 2 | gzip > /opt/django_peo_dumps/json/peo.$(date +"%Y-%m-%d_%H:%M:%S").json.gz
./manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude csa --indent 2 | gzip > $BACKUP_DIR_JSON/$FNAME.json.gz
mysqldump -u $USERNAME --password=$PASSWORD $DB | gzip > $BACKUP_DIR_SQL/$FNAME.sql.gz
