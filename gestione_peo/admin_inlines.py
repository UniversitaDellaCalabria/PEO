from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import *


class DescrizioneIndicatoreAdminAbstract(admin.ModelAdmin):
    def get_anteprima_modulo_inserimento(self, obj):
        url = reverse('domande_peo:anteprima_modulo_inserimento',
                      args=(obj.indicatore_ponderato.bando.pk,
                            obj.pk))
        button = ("<button type='button' class='button' onClick="
                  "window.open('{}','winname',"
                  "'directories=no,titlebar=no,toolbar=no,location=no,"
                  "status=no,menubar=no,scrollbars=no,resizable=no,"
                  "width=890,height=600')"
                  ';><span class="icon">Vedi</span></button>').format(url)
        return  mark_safe(button)
    get_anteprima_modulo_inserimento.short_description = 'Anteprima'

    class Meta:
        abstract = True


class PunteggioMax_DescrizioneIndicatore_PosEconomicaModelForm(forms.ModelForm):
    class Meta:
        model = PunteggioMax_DescrizioneIndicatore_PosEconomica
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class PunteggioMax_DescrizioneIndicatore_PosEconomicaInline(admin.TabularInline):
    model = PunteggioMax_DescrizioneIndicatore_PosEconomica
    form = PunteggioMax_DescrizioneIndicatore_PosEconomicaModelForm
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


class PunteggioMaxIndicatorePonderatoPosizioneEconomicaInline(admin.TabularInline):
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


class Punteggio_DescrizioneIndicatore_TimeDeltaInline(admin.TabularInline):
    model = Punteggio_DescrizioneIndicatore_TimeDelta
    form = Punteggio_DescrizioneIndicatore_TimeDeltaModelForm
    extra = 0
    classes = ['collapse',]


class Punteggio_DescrizioneIndicatoreInline(admin.TabularInline):
    model = Punteggio_DescrizioneIndicatore
    extra = 0
    classes = ['collapse',]


class DescrizioneIndicatoreModelForm(forms.ModelForm):
    class Meta:
        model = DescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class ModuloInserimentoCampiModelForm(forms.ModelForm):
    class Meta:
        model = ModuloInserimentoCampi
        fields = ('__all__')


class ModuloInserimentoCampiInline(admin.TabularInline):
    model = ModuloInserimentoCampi
    sortable_field_name = "ordinamento"
    extra = 0
    form = ModuloInserimentoCampiModelForm
    classes = ['collapse',]


class DescrizioneIndicatoreAbstract(admin.TabularInline):
    def get_anteprima_modulo_inserimento(self, obj):
        url = reverse('domande_peo:anteprima_modulo_inserimento',
                      args=(obj.indicatore_ponderato.bando.pk,
                            obj.pk))
        button = ("<button type='button' class='button' onClick="
                  "window.open('{}','winname',"
                  "'directories=no,titlebar=no,toolbar=no,location=no,"
                  "status=no,menubar=no,scrollbars=no,resizable=no,"
                  "width=890,height=600')"
                  ';><span class="icon">Vedi</span></button>').format(url)
        return  mark_safe(button)
    get_anteprima_modulo_inserimento.short_description = 'Anteprima'


class AvvisoBandoInline(admin.TabularInline, ):
    model = AvvisoBando
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class ClausoleBandoInline(admin.TabularInline, ):
    model = ClausoleBando
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class DescrizioneIndicatoreInline(DescrizioneIndicatoreAbstract,
                                  admin.TabularInline, ):
    model = DescrizioneIndicatore
    sortable_field_name = "ordinamento"
    form = DescrizioneIndicatoreModelForm
    extra = 0
    classes = ['collapse',]
    inlines = [ Punteggio_DescrizioneIndicatoreInline,
                Punteggio_DescrizioneIndicatore_TimeDeltaInline,
                PunteggioMax_DescrizioneIndicatore_PosEconomicaInline,
                ModuloInserimentoCampiInline,
               ]
    readonly_fields = ['get_anteprima_modulo_inserimento']


# https://docs.djangoproject.com/en/2.0/ref/contrib/admin/#django.contrib.admin.InlineModelAdmin
class IndicatorePonderatoInline(admin.TabularInline):
    model = IndicatorePonderato
    form  = IndicatorePonderatoModelForm
    sortable_field_name = "ordinamento"
    inlines = [
                # DescrizioneIndicatoreInline,
                PunteggioMaxIndicatorePonderatoPosizioneEconomicaInline, ]

    # This controls the number of extra forms the formset will display in addition to the initial forms.
    extra = 0
    classes = ['collapse',]


class Punteggio_TitoloStudioModelForm(forms.ModelForm):
    class Meta:
        model = Punteggio_TitoloStudio
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class Punteggio_TitoloStudioInline(admin.TabularInline):
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


class CategorieDisabilitate_TitoloStudioInline(admin.TabularInline):
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


class Punteggio_Anzianita_ServizioInline(admin.TabularInline):
    model = Punteggio_Anzianita_Servizio
    form = Punteggio_Anzianita_ServizioModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class Punteggio_SubDescrizioneIndicatore_TimeDeltaModelForm(forms.ModelForm):
    class Meta:
        model = Punteggio_SubDescrizioneIndicatore_TimeDelta
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class Punteggio_SubDescrizioneIndicatore_TimeDeltaInline(admin.TabularInline):
    model = Punteggio_SubDescrizioneIndicatore_TimeDelta
    form = Punteggio_SubDescrizioneIndicatore_TimeDeltaModelForm
    extra = 0
    classes = ['collapse',]


class Punteggio_SubDescrizioneIndicatoreInline(admin.TabularInline):
    model = Punteggio_SubDescrizioneIndicatore
    extra = 0
    classes = ['collapse',]


class PunteggioMax_SubDescrizioneIndicatore_PosEconomicaModelForm(forms.ModelForm):
    class Meta:
        model = PunteggioMax_SubDescrizioneIndicatore_PosEconomica
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class PunteggioMax_SubDescrizioneIndicatore_PosEconomicaInline(admin.TabularInline):
    model = PunteggioMax_SubDescrizioneIndicatore_PosEconomica
    form = PunteggioMax_SubDescrizioneIndicatore_PosEconomicaModelForm
    sortable_field_name = "ordinamento"
    extra = 0
    classes = ['collapse',]


class SubDescrizioneIndicatoreModelForm(forms.ModelForm):
    class Meta:
        model = SubDescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput()}


class SubDescrizioneIndicatoreInline(admin.TabularInline):
    model = SubDescrizioneIndicatore
    sortable_field_name = "ordinamento"
    form = SubDescrizioneIndicatoreModelForm
    extra = 0
    classes = ['collapse',]
    inlines = [Punteggio_SubDescrizioneIndicatoreInline,
               Punteggio_SubDescrizioneIndicatore_TimeDeltaInline,
               PunteggioMax_SubDescrizioneIndicatore_PosEconomicaInline]


class CategorieDisabilitate_DescrizioneIndicatoreModelForm(forms.ModelForm):
    class Meta:
        model = CategorieDisabilitate_DescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput(),
                   'posizione_economica': forms.CheckboxSelectMultiple()}


class CategorieDisabilitate_DescrizioneIndicatoreInline(admin.TabularInline):
    model = CategorieDisabilitate_DescrizioneIndicatore
    form = CategorieDisabilitate_DescrizioneIndicatoreModelForm
    extra = 0
    classes = ['collapse',]


class RuoliDisabilitati_DescrizioneIndicatoreModelForm(forms.ModelForm):

    class Meta:
        model = RuoliDisabilitati_DescrizioneIndicatore
        fields = ('__all__')
        widgets = {'ordinamento': forms.HiddenInput(),
                   'ruolo': forms.CheckboxSelectMultiple()}


class RuoliDisabilitati_DescrizioneIndicatoreInline(admin.TabularInline):
    model = RuoliDisabilitati_DescrizioneIndicatore
    form = RuoliDisabilitati_DescrizioneIndicatoreModelForm
    extra = 0
    classes = ['collapse',]
