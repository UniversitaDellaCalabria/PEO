from datetime import datetime

from django.conf import settings
from django.utils import timezone

def differenza_date_in_mesi_aru(dt, now=None):
    """
    calcola quanti mesi sono trascorsi tra la data dt e new
    secondo il modello ARU, dove per mese si intendono almeno 15 giorni + 1
    all'interno dell'ultimo mese considerabile.
    """
    if now:
        mo = now
    else:
        mo = timezone.localtime()

    anni = mo.year - dt.year
    mesi =  mo.month - dt.month
    giorni = mo.day - dt.day + 1

    if giorni > 15:
        mesi = mesi + 1
    elif giorni <= -15:
        mesi = mesi - 1

    return mesi + 12*anni

def parse_date_string(dt):
    """
    Crea un date() a partire da una stringa.
    Il formato deve rispettare le limitazioni imposte nel SETTINGS
    """
    if not dt:
        return False

    for formato in settings.DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(dt, formato).date()
        except ValueError:
            pass
    raise ValueError('Formato della data non valido')

def text_as_html(text):
    """
    Sostituisce '\n' con '<br>' in un testo
    """
    return text.replace('\n', '<br>')
