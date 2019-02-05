import datetime, pytz

from django.shortcuts import render_to_response, get_object_or_404
from django import template

register = template.Library()

@register.simple_tag
def show_domanda_button(bando, dipendente):
    if not bando.is_in_corso():
        return False
    if dipendente.utente.is_staff:
        return bando in dipendente.idoneita_peo_staff()
    return bando in dipendente.idoneita_peo_attivata()
