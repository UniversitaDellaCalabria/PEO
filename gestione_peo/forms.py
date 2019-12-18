import datetime
import magic
import os

from django import forms
from django.conf import settings
from django.forms.fields import FileField
from django.template.defaultfilters import filesizeformat
from django.utils import timezone

from django_form_builder.dynamic_fields import format_field_name
from django_form_builder.forms import BaseDynamicForm

from . import peo_formfields
from . settings import (ETICHETTA_INSERIMENTI_ID,
                        ETICHETTA_INSERIMENTI_LABEL,
                        ETICHETTA_INSERIMENTI_HELP_TEXT)


class PeoDynamicForm(BaseDynamicForm):
    def __init__(self,
                 constructor_dict={},
                 custom_params={},
                 *args,
                 **kwargs):

        self.fields = {}
        self.domanda_bando = custom_params.get('domanda_bando')
        self.descrizione_indicatore = custom_params.get('descrizione_indicatore')

        # Inserimento manuale del field ETICHETTA
        etichetta_id = format_field_name(ETICHETTA_INSERIMENTI_ID)
        etichetta_data = {'required' : True,
                          'label': ETICHETTA_INSERIMENTI_LABEL,
                          'help_text': ETICHETTA_INSERIMENTI_HELP_TEXT}
        etichetta_field = getattr(peo_formfields,
                                  'CustomCharField')(**etichetta_data)
        self.fields[etichetta_id] = etichetta_field
        self.fields[etichetta_id].initial = self.descrizione_indicatore

        super().__init__(fields_source=peo_formfields,
                         initial_fields=self.fields,
                         constructor_dict=constructor_dict,
                         custom_params=custom_params,
                         *args, **kwargs)

    def clean(self, *args, **kwargs):
        super().clean(domanda_bando=self.domanda_bando)
