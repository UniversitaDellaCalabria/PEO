import datetime, pytz

from django.shortcuts import get_object_or_404
from django import template

register = template.Library()

@register.simple_tag
def descrizione_indicatore_available(descrizione_indicatore, cateco, ruolo):
    return descrizione_indicatore.is_available_for_cat_role(cateco, ruolo)
