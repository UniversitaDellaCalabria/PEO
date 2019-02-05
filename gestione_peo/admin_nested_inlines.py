import nested_admin

from django import forms
from django.contrib import admin

from .admin_inlines import DescrizioneIndicatoreAbstract
from .models import *


class PunteggioMax_DescrizioneIndicatore_PosEconomicaModelForm(forms.ModelForm):
    class Meta:
        model = PunteggioMax_DescrizioneIndicatore_PosEconomica
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class PunteggioMax_SubDescrizioneIndicatore_PosEconomicaModelForm(forms.ModelForm):
    class Meta:
        model = PunteggioMax_SubDescrizioneIndicatore_PosEconomica
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class PunteggioMax_DescrizioneIndicatore_PosEconomicaNestedInline(nested_admin.NestedTabularInline):
    model = PunteggioMax_DescrizioneIndicatore_PosEconomica
    form = PunteggioMax_DescrizioneIndicatore_PosEconomicaModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class PunteggioMax_SubDescrizioneIndicatore_PosEconomicaNestedInline(nested_admin.NestedTabularInline):
    model = PunteggioMax_SubDescrizioneIndicatore_PosEconomica
    form = PunteggioMax_SubDescrizioneIndicatore_PosEconomicaModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class IndicatorePonderatoModelForm(forms.ModelForm):
    class Meta:
        model = IndicatorePonderato
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class PunteggioMaxIndicatorePonderatoPosizioneEconomicaModelForm(forms.ModelForm):
    class Meta:
        model = PunteggioMax_IndicatorePonderato_PosEconomica
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class PunteggioMaxIndicatorePonderatoPosizioneEconomicaNestedInline(nested_admin.NestedTabularInline):
    model = PunteggioMax_IndicatorePonderato_PosEconomica
    sortable_field_name = "ordinamento"
    extra = 0
    form = PunteggioMaxIndicatorePonderatoPosizioneEconomicaModelForm
    classes = ['collapse',]


class Punteggio_DescrizioneIndicatore_TimeDeltaModelForm(forms.ModelForm):
    class Meta:
        model = Punteggio_DescrizioneIndicatore_TimeDelta
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class Punteggio_SubDescrizioneIndicatore_TimeDeltaModelForm(forms.ModelForm):
    class Meta:
        model = Punteggio_SubDescrizioneIndicatore_TimeDelta
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class Punteggio_DescrizioneIndicatore_TimeDeltaNestedInline(nested_admin.NestedTabularInline):
    model = Punteggio_DescrizioneIndicatore_TimeDelta
    form = Punteggio_DescrizioneIndicatore_TimeDeltaModelForm
    extra = 0
    classes = ['collapse',]


class Punteggio_SubDescrizioneIndicatore_TimeDeltaNestedInline(nested_admin.NestedTabularInline):
    model = Punteggio_SubDescrizioneIndicatore_TimeDelta
    form = Punteggio_SubDescrizioneIndicatore_TimeDeltaModelForm
    extra = 0
    classes = ['collapse',]


class Punteggio_DescrizioneIndicatoreNestedInline(nested_admin.NestedTabularInline):
    model = Punteggio_DescrizioneIndicatore
    extra = 0
    classes = ['collapse',]


class Punteggio_SubDescrizioneIndicatoreNestedInline(nested_admin.NestedTabularInline):
    model = Punteggio_SubDescrizioneIndicatore
    extra = 0
    classes = ['collapse',]


class DescrizioneIndicatoreModelForm(forms.ModelForm):
    class Meta:
        model = DescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class SubDescrizioneIndicatoreModelForm(forms.ModelForm):
    class Meta:
        model = SubDescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class ModuloInserimentoCampiModelForm(forms.ModelForm):
    class Meta:
        model = ModuloInserimentoCampi
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class ModuloInserimentoCampiNestedInline(nested_admin.NestedTabularInline):
    model = ModuloInserimentoCampi
    sortable_field_name = "ordinamento"
    extra = 0
    form = ModuloInserimentoCampiModelForm
    classes = ['collapse',]


class DescrizioneIndicatoreNestedInline(DescrizioneIndicatoreAbstract,
                                  nested_admin.NestedTabularInline, ):
    model = DescrizioneIndicatore
    sortable_field_name = "ordinamento"
    form = DescrizioneIndicatoreModelForm
    extra = 0
    classes = ['collapse',]
    NestedInlines = [ Punteggio_DescrizioneIndicatoreNestedInline,
                Punteggio_DescrizioneIndicatore_TimeDeltaNestedInline,
                PunteggioMax_DescrizioneIndicatore_PosEconomicaNestedInline,
                ModuloInserimentoCampiNestedInline]
    readonly_fields = ['get_anteprima_modulo_inserimento']


class SubDescrizioneIndicatoreNestedInline(nested_admin.NestedTabularInline):
    model = SubDescrizioneIndicatore
    sortable_field_name = "ordinamento"
    form = SubDescrizioneIndicatoreModelForm
    extra = 0
    classes = ['collapse',]
    NestedInlines = [Punteggio_SubDescrizioneIndicatoreNestedInline,
                     Punteggio_SubDescrizioneIndicatore_TimeDeltaNestedInline,
                     PunteggioMax_SubDescrizioneIndicatore_PosEconomicaNestedInline]


class IndicatorePonderatoNestedInline(nested_admin.NestedTabularInline):
    model = IndicatorePonderato
    form  = IndicatorePonderatoModelForm
    sortable_field_name = "ordinamento"
    NestedInlines = [ 
                     # DescrizioneIndicatoreNestedInline,
                     PunteggioMaxIndicatorePonderatoPosizioneEconomicaNestedInline,]
    # This controls the number of extra forms the formset will display in addition to the initial forms.
    extra = 0
    classes = ['collapse',]


class ClausoleBandoNestedInline(nested_admin.NestedTabularInline):
    model = ClausoleBando
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class Punteggio_TitoloStudioModelForm(forms.ModelForm):
    class Meta:
        model = Punteggio_TitoloStudio
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class Punteggio_TitoloStudioNestedInline(nested_admin.NestedTabularInline):
    model = Punteggio_TitoloStudio
    form = Punteggio_TitoloStudioModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class CategorieDisabilitate_TitoloStudioModelForm(forms.ModelForm):
    class Meta:
        model = CategorieDisabilitate_TitoloStudio
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class CategorieDisabilitate_TitoloStudioNestedInline(nested_admin.NestedTabularInline):
    model = CategorieDisabilitate_TitoloStudio
    form = CategorieDisabilitate_TitoloStudioModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class Punteggio_Anzianita_ServizioModelForm(forms.ModelForm):
    class Meta:
        model = Punteggio_Anzianita_Servizio
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class Punteggio_Anzianita_ServizioNestedInline(nested_admin.NestedTabularInline):
    model = Punteggio_Anzianita_Servizio
    form = Punteggio_Anzianita_ServizioModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class CategorieDisabilitate_DescrizioneIndicatoreModelForm(forms.ModelForm):
    class Meta:
        model = CategorieDisabilitate_DescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput(),
                   'posizione_economica': forms.CheckboxSelectMultiple()}


class CategorieDisabilitate_DescrizioneIndicatoreNestedInline(nested_admin.NestedTabularInline):
    model = CategorieDisabilitate_DescrizioneIndicatore
    form = CategorieDisabilitate_DescrizioneIndicatoreModelForm
    sortable_field_name = "ordinamento"
    extra = 1
    max_num = 1
    classes = ['collapse',]


class RuoliDisabilitati_DescrizioneIndicatoreModelForm(forms.ModelForm):
    class Meta:
        model = RuoliDisabilitati_DescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput(),}
                   #'ruolo': forms.CheckboxSelectMultiple()}
                
class RuoliDisabilitati_DescrizioneIndicatoreNestedInline(nested_admin.NestedTabularInline):
    model = RuoliDisabilitati_DescrizioneIndicatore
    form = RuoliDisabilitati_DescrizioneIndicatoreModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    #max_num = 1
    classes = ['collapse',]
