from django import template

register = template.Library()

@register.simple_tag
def domanda_bando_num_max_descrind(domanda_bando, descr_ind):
    if descr_ind.limite_inserimenti:
        mdb_presenti = domanda_bando.num_mdb_tipo_inseriti(descr_ind)
        return mdb_presenti == descr_ind.numero_inserimenti
