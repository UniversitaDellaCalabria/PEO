from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField

from .models import *
from gestione_peo.models import *


class GenericPeoForm(forms.Form):
    numero_di_protocollo =  forms.CharField(label='Numero di Protocollo',
                                            max_length='8',
                                            widget=forms.TextInput(attrs={'class':'CUSTOM'}))
    anno_protocollo = forms.IntegerField(widget=forms.TextInput(attrs={'class':'CUSTOM'}))
    data_inizio = forms.DateField(widget=forms.TextInput(attrs={'type':'date',
                                                                'class':'CUSTOM'}))
    data_fine = forms.DateField(widget=forms.TextInput(attrs={'type':'date',
                                                              'class':'CUSTOM'}))


class AccettazioneClausoleForm(forms.Form):
	accettazione = forms.BooleanField(label='')
	
class AllegatoForm(forms.Form):
    allegato = forms.FileField(label='Allegato')
                        
    
class TitoliForm(forms.Form):
    denominazione_titolo = forms.CharField(label='Denominazione del Titolo',
                                           max_length='200')
    tipologia_titolo = forms.ModelChoiceField(queryset=Bando.objects.all(), 
                                              label='Tipologia Titolo')

class TitoloPeoForm(AllegatoForm, TitoliForm, GenericPeoForm):
    pass


class IncaricoPeoForm(AllegatoForm, TitoliForm, GenericPeoForm):
    pass


class PrestazioniIndividualiForm(AllegatoForm, TitoliForm, GenericPeoForm):
    pass
