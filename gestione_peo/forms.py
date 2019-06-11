import datetime
import magic
import os

from django import forms
from django.conf import settings
from django.forms.fields import FileField
from django.template.defaultfilters import filesizeformat
from django.utils import timezone

from . import peo_formfields
from .settings import (ETICHETTA_INSERIMENTI_ID,
                       ETICHETTA_INSERIMENTI_LABEL,
                       ETICHETTA_INSERIMENTI_HELP_TEXT,
                       NUMERAZIONI_CONSENTITE)


def format_field_name(field_name):
    return field_name.replace(' ','_').lower()


class PeoDynamicForm(forms.Form):
    def __init__(self,
                 constructor_dict,
                 domanda_bando=None,
                 descrizione_indicatore=None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        # HiddenField con riferimento alla domanda
        if domanda_bando:
            constructor_dict['Domanda Bando ID'] = ('CustomHiddenField',
                                                    {'label': ''},
                                                    domanda_bando.pk)
        self.domanda_bando = domanda_bando

        # Inserimento manuale del field ETICHETTA
        etichetta_id = format_field_name(ETICHETTA_INSERIMENTI_ID)
        etichetta_data = {'required' : True,
                          'label': ETICHETTA_INSERIMENTI_LABEL,
                          'help_text': ETICHETTA_INSERIMENTI_HELP_TEXT}
        etichetta_field = getattr(peo_formfields,
                                  'CustomCharField')(**etichetta_data)
        self.fields[etichetta_id] = etichetta_field
        self.fields[etichetta_id].initial = descrizione_indicatore

        for key, value in constructor_dict.items():
            field_id = format_field_name(key)
            data_kwargs = {'label': key.title()}
            # add custom attrs
            data_kwargs.update(value[1])
            custom_field = getattr(peo_formfields, value[0])(**data_kwargs) \
                                   if hasattr(peo_formfields, value[0]) else None
            if custom_field:
                custom_field.define_value(domanda_bando,
                                          descrizione_indicatore,
                                          value[2])
                fields = custom_field.get_fields()
                for field in fields:
                    name = field_id
                    if hasattr(field, 'name'):
                        name = getattr(field, 'name')
                    self.fields[name]= field

    def remove_not_compiled_fields(self):
        """
        Rimuove da un form compilato tutti i campi non compilati
        Viene usato nel metodo get_form
        """
        to_be_removed = []
        for field in self:
            if not field.value():
                to_be_removed.append(field.name)
        for i in to_be_removed:
            del self.fields[i]

    def remove_files(self, allegati = None):
        """
        Rimuove tutti i FileFields
        viene usato in modifica_form se allegati già presenti
        """
        to_be_removed = []
        for field in self.fields:
            if isinstance(allegati, dict):
                # rimuove solo i fields allegati/files specificati
                if field in allegati:
                    to_be_removed.append(field)
            elif isinstance(self.fields[field], FileField):
                # rimuove tutti i fields  allegati/files
                to_be_removed.append(field)

        for i in to_be_removed:
            del self.fields[i]

    @staticmethod
    def validate_attachment(content):
        if content.content_type not in settings.PERMITTED_UPLOAD_FILETYPE:
            msg_tmpl = ("Per favore esegui l'upload di soli file in "
                        "formato PDF. Attualmente questo è '{}'")
            return msg_tmpl.format(content.content_type)
        elif content.size > int(settings.MAX_UPLOAD_SIZE):
            msg_tmpl = ("Per favore mantieni la dimensione del file "
                        "entro {}. Attualmente questo è {}")
            return msg_tmpl.format(filesizeformat(settings.MAX_UPLOAD_SIZE),
                                   filesizeformat(content.size))
        elif len(content._name) > settings.ATTACH_NAME_MAX_LEN:
            msg_tmpl = ("Per favore usa una lunghezza massima del nome "
                        "dell'allegato inferiore a {}. Attualmente hai "
                        "inserito un nome di {} caratteri")
            return msg_tmpl.format(settings.ATTACH_NAME_MAX_LEN,
                                   len(content._name))

    def check_file(self, content):
        err =  self.validate_attachment(content)
        if err:
            self.add_error(content.field_name, err)

    def get_labeled_errors(self):
        self.is_valid()
        d = {}
        for field_name in self.errors:
            field = self.fields[field_name]
            d[field.label] = self.errors[field_name]
        return d

    def clean(self):
        cleaned_data = super().clean()
        for fname in self.fields:
            field = self.fields[fname]
            if hasattr(field, 'parent'):
                field = getattr(field, 'parent')
            errors = field.raise_error(self.domanda_bando, fname, cleaned_data)
            if errors:
                self.add_error(fname, errors)
                continue

            # Check sui files (FileField)
            if isinstance(self.fields[fname], FileField):
                content = self.cleaned_data[fname]
                if content:
                    self.check_file(content)
