import datetime

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django_admin_multiple_choice_list_filter.list_filters import MultipleChoiceListFilter
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from . models import *
from .peo_methods import bando_redazione


if 'csa' in settings.INSTALLED_APPS:
    from csa.models import RUOLI
else:
    RUOLI = settings.RUOLI


class RuoloListFilter(MultipleChoiceListFilter):
    title = 'Ruolo'
    parameter_name = 'ruolo'

    def lookups(self, request, model_admin):
        return [(k, v) for k,v in sorted(RUOLI)]

    def queryset(self, request, queryset):
        pk_list = []
        if request.GET.get(self.parameter_name):
            for value in request.GET[self.parameter_name].split(','):
                kwargs = {self.parameter_name: value}
                q = queryset.filter(**kwargs)
                for dip in q.values_list('pk'):
                    pk_list.append(dip[0])
            return queryset.filter(pk__in=pk_list)


class CategoriaListFilter(MultipleChoiceListFilter):
    title = 'Categoria Pos.Economica'
    parameter_name = 'livello__posizione_economica__pk'

    def lookups(self, request, model_admin):
        return [(y.pk,y.nome) for y in PosizioneEconomica.objects.all()]

    def queryset(self, request, queryset):
        pk_list = []
        if request.GET.get(self.parameter_name):
            for value in request.GET[self.parameter_name].split(','):
                kwargs = {self.parameter_name: value}
                q = queryset.filter(**kwargs)
                for dip in q.values_list('pk'):
                    pk_list.append(dip[0])
            return queryset.filter(pk__in=pk_list)


# https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.ModelAdmin.list_filter
class IdoneiPeoListFilter(admin.SimpleListFilter):
    title = 'Idonei PEO'
    parameter_name = 'idoneita_peo'

    def lookups(self, request, model_admin):
        return (('1', 'Si'),
                ('0', 'No'))

    def queryset(self, request, queryset):
        idonei_pk = []
        if not self.value() : return
        messages.add_message(request, messages.INFO,
                             'Filtro idoneità per bando: {}'.format(bando_redazione()))
        # preservo i cessati di almeno un anno indietro (timezone.timedelta(365)), perchè aventi diritto
        for idoneo in queryset\
        .filter(data_cessazione_contratto__gte=(timezone.localtime()-timezone.timedelta(365))):
            try:
                if idoneo.idoneita_peo():
                    idonei_pk.append(idoneo.pk)
            except Exception as e:
                messages.add_message(request, messages.ERROR, '{}, ERRORE: {}'.format(idoneo, e))
        if self.value() == '1':
            return queryset.filter(pk__in=idonei_pk)
        if self.value() == '0':
            return queryset.exclude(pk__in=idonei_pk)
