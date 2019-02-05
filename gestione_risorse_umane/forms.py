from django import forms
from django.conf import settings
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField
from django.template.defaultfilters import filesizeformat

from .models import *

class CartaIdentitaForm(forms.Form):
    carta_identita_front = forms.FileField(label='Fronte')
    carta_identita_retro = forms.FileField(label='Retro')

    def clean(self):
        cleaned_data = super().clean()
        for field_name in ('carta_identita_front', 'carta_identita_retro'):
            content = self.cleaned_data.get(field_name)
            # rimuovere caratteri di encoding altrimenti il download fallisce lato ws
            if not content:
                msg = "E' incorso un errore in uno dei due file caricati, prego reinserire i files"
                self.add_error(field_name, msg)
                return
            content._name = content._name.encode('ascii', errors='ignore').decode('ascii')

            if content.content_type not in settings.IMG_PERMITTED_UPLOAD_FILETYPE:
                msg_tmpl = "Per favore esegui l'upload di soli file nel seguente formato: '{}'"
                msg = msg_tmpl.format(', '.join(settings.IMG_PERMITTED_UPLOAD_FILETYPE))
                self.add_error(field_name, msg)
            elif content._size > int(settings.IMG_MAX_UPLOAD_SIZE):
                msg_tmpl = "Per favore mantieni la dimensione del file entro {}. {} è {}"
                msg = msg_tmpl.format(filesizeformat(settings.MAX_UPLOAD_SIZE),
                                      content._name,
                                      filesizeformat(content._size))
                self.add_error(field_name, msg)
            elif len(content._name) > settings.ATTACH_NAME_MAX_LEN:
                msg_tmpl = ("Per favore usa una lunghezza massima "
                            "dell'allegato inferiore a {}. Attualmente questa è {}")
                msg = msg_tmpl.format(settings.ATTACH_NAME_MAX_LEN,
                                      len(content._name))
                self.add_error(field_name, msg)
