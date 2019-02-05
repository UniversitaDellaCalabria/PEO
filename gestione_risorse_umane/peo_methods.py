import datetime

from django.apps import apps
from django.db.models import Q
from django.utils import timezone
from unical_template.utils import differenza_date_in_mesi_aru
from csa.models import CARRIERA_FIELDS_MAP
from .decorators import is_apps_installed

def bando_redazione():
    bando_peo_model = apps.get_model(app_label='gestione_peo', model_name='Bando')
    # bando = bando_peo_model.objects.filter(Q(redazione=True)|\
                                           # Q(collaudo=True)|\
                                           # Q(pubblicato=True) )
    bando = bando_peo_model.objects.filter(redazione=True)
    if not bando:
        # nessun bando in Redazione, nessun calcolo interno verrà effettuato
        return False
    else: bando = bando.latest('data_inizio')
    return bando

class PeoMethods(object):
    @is_apps_installed(['domande_peo'])
    def get_domande_progressione(self):
        """
        torna l'ultima domanda
        """
        domanda_peo_model = apps.get_model(app_label='domande_peo',
                                           model_name='DomandaBando')
        domande_peo = domanda_peo_model.objects.filter(dipendente=self,
                                                       is_active=True).order_by('-created')
        return domande_peo

    def get_last_domanda_progressione(self):
        dp = self.get_domande_progressione()
        if dp: return dp.latest('data_chiusura')

    def get_data_progressione(self, debug=False):
        # torna la data in cui è avvenuta l'ultima progressione
        if self.data_ultima_progressione_manuale:
            return self.data_ultima_progressione_manuale

        c = self.get_carriera_csa()
        if not c: return False

        if debug:
            for i in c:
                print(i['data_inizio'],
                      i['inquadramento'],
                      i['attività'])

        _ultima = {'dt_ini': c[0]['data_inizio'],
                   'inquadr': c[0]['inquadramento']}
        for i in c:
            # se esiste nella carriera un evento di fine rapporto, non andare oltre
            # 0020 è troppo brusco, non posso usarlo
            # if i['attivita'] in ['0020', ]:
                # break
            if _ultima['inquadr'] == i['inquadramento']:
                _ultima['dt_ini'] = i['data_inizio']

        return timezone.get_current_timezone().localize(_ultima['dt_ini'])

    @is_apps_installed(['gestione_peo', ])
    def idoneita_peo(self):
        """
            torna se idoneo secondo la valutazione del sistema
            sulla base dell'ultimo bando creato
        """
        # if not self.get_in_servizio(): return False
        bando = bando_redazione()
        if not bando or self.disattivato: return False

        # Se ad oggi non sono stati maturati gli anni minimi di servizio
        # specificati nel bando
        data_presa_servizio = self.get_data_presa_servizio_csa().date()
        if (bando.data_validita_titoli_fine - data_presa_servizio) < datetime.timedelta(days=(365*bando.anni_servizio_minimi)):
            return False

        # Verifico che il dipendente abbia o meno fatto domande di progressione
        # Se non ne ha eseguito nessuna, allora lo considero idoneo
        domande_peo = self.get_domande_progressione()
        if domande_peo:
            domanda_peo = domande_peo.latest('data_chiusura')

        if not self.get_data_progressione():
            # non ha fatto alcuna progressione
            return True

        # Se l'ultima progressione effettuata non rispetta i termini del bando
        # specificati dal campo "ultima_progressione"
        if self.get_data_progressione().date() > bando.ultima_progressione:
            return False
        return True

    # https://stackoverflow.com/questions/28513528/passing-arguments-to-model-methods-in-django-templates?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
    # fare tornare tutti i bandi ai quali si è attivi e creare template tag
    @is_apps_installed(['gestione_peo', 'domande_peo'])
    def idoneita_peo_attivata(self):
        """
        torna la lista dei bandi per i quali il dipendente risulta
        idoneo a partecipare
        """
        bando_peo_model = apps.get_model(app_label='gestione_peo',
                                         model_name='Bando')
        bandi = bando_peo_model.objects.filter(Q(redazione=True)|\
                                               Q(collaudo=True)|\
                                               Q(pubblicato=True) )
        if not bandi: return False
        abilitazione_peo_model = apps.get_model(app_label='domande_peo',
                                                model_name='AbilitazioneBandoDipendente')
        abilitazioni = []
        for i in bandi:
            abilitazione = abilitazione_peo_model.objects.filter(dipendente=self,
                                                                 bando=i).first()
            if not abilitazione: continue
            if abilitazione.bando:
                abilitazioni.append(abilitazione.bando.pk)
        return bandi.filter(pk__in=abilitazioni)

    @is_apps_installed(['gestione_peo', 'domande_peo'])
    def idoneita_peo_staff(self):
        """
        Se l'utente fa parte dello staff,
        torna tutti i bandi in collaudo (anche se non abilitato)
        e quelli per cui è abilitato a partecipare
        """
        if not self.utente: return False
        if not self.utente.is_staff: return False
        bando_peo_model = apps.get_model(app_label='gestione_peo',
                                         model_name='Bando')
        bandi_pk = [i.pk for i in self.idoneita_peo_attivata()]
        bandi_in_collaudo = [i.pk for i in bando_peo_model.objects.filter(collaudo=True)]
        bandi_pk.extend(bandi_in_collaudo)
        return bando_peo_model.objects.filter(pk__in=bandi_pk)

    def get_ultima_progressione_mesi(self):
        """
        torna i mesi trascorsi dall'ultima progressione effettuata, fino a oggi
        """
        ultima_progressione = self.get_data_progressione()
        if not ultima_progressione:
            return False
        return differenza_date_in_mesi_aru(ultima_progressione)
