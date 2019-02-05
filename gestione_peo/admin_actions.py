import io
import json

from django.apps import apps
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponse

from .models import *
from django_auto_serializer.auto_serializer import (SerializableInstance,
                                                    ImportableSerializedInstance)


def duplica_bando(modeladmin, request, queryset):
    for bando in queryset:
        try:
            si = SerializableInstance(bando)
            st = si.serialize_tree()
        except Exception as e:
            msg = '{} duplicazione fallita: {}'
            messages.add_message(request, messages.WARNING,
                                 msg.format(bando, e))
        try:
            isi = ImportableSerializedInstance(si.dict)
            isi.save()
        except Exception as e:
            msg = '{} duplicazione fallita: {}'
            messages.add_message(request, messages.WARNING,
                                 msg.format(bando, e))

        msg = '{} correttamente duplicato.'
        messages.add_message(request, messages.INFO,
                             msg.format(bando))
duplica_bando.short_description = "Duplica il Bando e la sua Configurazione"


def scarica_template_bando(modeladmin, request, queryset):
    iofile = io.StringIO()
    bandi_labels = []
    for bando in queryset:
        try:
            si = SerializableInstance(bando)
            st = si.serialize_tree()
            iofile.write(json.dumps(si.dict, indent=2))
        except Exception as e:
            msg = '{} duplicazione fallita: {}'
            messages.add_message(request, messages.WARNING,
                                 msg.format(bando, e))
        bandi_labels.append(bando.slug)
    file_name = 'peo_template_bando_{}.json'.format('_'.join(bandi_labels))
    iofile.seek(0)
    response = HttpResponse(iofile.read())
    response['content_type'] = 'application/force-download'
    response['Content-Disposition'] = 'attachment; filename={}'.format(file_name)
    response['X-Sendfile'] = file_name
    return response
scarica_template_bando.short_description = "Scarica Template Bando"
