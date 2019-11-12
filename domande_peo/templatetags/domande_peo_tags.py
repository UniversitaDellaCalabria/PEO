from django import template

from django_form_builder.models import SavedFormContent
from django_form_builder.utils import get_allegati
from gestione_peo.settings import ETICHETTA_INSERIMENTI_ID

register = template.Library()

@register.simple_tag
def domanda_bando_num_max_descrind(domanda_bando, descr_ind):
    if descr_ind.limite_inserimenti:
        mdb_presenti = domanda_bando.num_mdb_tipo_inseriti(descr_ind)
        return mdb_presenti == descr_ind.numero_inserimenti

@register.simple_tag
def domanda_bando_readonly(compiled_form_source):
    form = compiled_form_source.compiled_form()
    return SavedFormContent.compiled_form_readonly(form=form,
                                                   fields_to_remove=[ETICHETTA_INSERIMENTI_ID,])

@register.simple_tag
def get_allegati_modulo(mdb):
    return get_allegati(mdb)
