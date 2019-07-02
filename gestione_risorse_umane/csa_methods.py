import re

from django.apps import apps
from django.core.cache import cache
from django.utils import timezone

from csa.models import (_get_matricola,
                        CARRIERA_FIELDS_MAP,
                        INCARICHI_FIELDS_MAP)
from .decorators import is_apps_installed
from .exceptions import CSAException


class CSAMethods(object):
    """
    Classe con i metodi di interrogazione carriere dipendenti
    """
    def get_anagrafica_csa(self):
        cache_name = '{}_{}'.format(_get_matricola(self.matricola), 'anagrafica_csa')
        csa_cache = cache.get(cache_name)
        if csa_cache: return csa_cache

        csa_model = apps.get_model(app_label='csa', model_name='V_ANAGRAFICA')
        anagrafica_csa = csa_model.objects.filter(matricola=_get_matricola(self.matricola)).first()
        if not anagrafica_csa:
            raise CSAException(message=('{} non presenta alcuna '
                                        'anagrafica in CSA, è possibile '
                                        'che sia andato in pensione e '
                                        'non più disponibile in peo CSA.').format(self),
                               errors=['self.get_anagrafica_csa() non torna niente.',])
        cache.set(cache_name, anagrafica_csa)
        return anagrafica_csa

    def get_carriera_docente_csa(self):
        anagrafica_csa = self.get_anagrafica_csa()
        carriera = anagrafica_csa.get_carriera_docente_view()
        return carriera

    def get_carriera_csa(self):
        anagrafica_csa = self.get_anagrafica_csa()
        carriera = anagrafica_csa.get_carriera_docente_view() or anagrafica_csa.get_carriera_view()
        if not carriera:
            raise CSAException(message=('Il dipendente non presenta '
                                        'alcuna carriera in CSA.'),
                               errors=['anagrafica_csa.get_carriera_view() non torna niente.',])
        return carriera

    def get_first_carriera_csa(self):
        c = self.get_carriera_csa()
        if c:
            primo_evento = c[0]
            for i in c:
                # prelevelo il minore, se data_inizio o data_inizio_rapporto
                if i['data_inizio_rapporto'] < i['data_inizio']:
                    field = 'data_inizio_rapporto'
                else:
                    field = 'data_inizio'
                if i[field] < primo_evento[field]:
                    primo_evento = i
            return primo_evento

    def get_last_carriera_csa(self):
        c = self.get_carriera_csa()
        if c:
            ultimo_evento = c[0]
            for i in c:
                # prelevelo il minore, se data_inizio o data_inizio_rapporto
                if i['data_inizio_rapporto'] < i['data_inizio']:
                    field = 'data_inizio_rapporto'
                else:
                    field = 'data_inizio'
                if i[field] > ultimo_evento[field]:
                    ultimo_evento = i
            return ultimo_evento

    def get_profilo_csa(self):
        c = self.get_last_carriera_csa()
        profilo = c.get('descr_profilo') or c.get('ds_ruolo')
        return profilo

    def get_afforg_csa(self):
        c = self.get_last_carriera_csa()
        if c:
            return c.get('descr_aff_org') or c.get('descr_sede')

    def get_sede_csa(self):
        c = self.get_last_carriera_csa()
        if c: return c['descr_sede']

    def get_ruolo_csa(self):
        c = self.get_anagrafica_csa()
        if c: return self.get_last_carriera_csa()['ruolo']

    def get_inquadramento_csa(self):
        try:
            c = self.get_anagrafica_csa()
        except Exception as e:
            print(e)
            return
        c =  self.get_last_carriera_csa()
        if c: return (c['inquadramento'], c['descr_inquadramento'])

    def extract_inquadramento_csa(self):
        inq = self.get_inquadramento_csa()
        if not inq: return
        regexp = ["(?P<cat>EP)(?P<liv>[0-9]+)",
                  "(?P<cat>[0]*[a-z1-9]+)([' ']*)?(?P<liv>[0-9]*)"]
        v = None
        for exp in regexp:
            r = re.search(exp, inq[0], re.I)
            if r:
                v = r.groupdict()
                break
        if not v: raise Exception("extract_inquadramento_csa cannot extract: {}".format(inq))
        v["descr"] = inq[1]
        return v

    def set_inquadramento_from_csa(self):
        """
        Salva posizione e livello - categoria del dipendente
        """
        inq = self.extract_inquadramento_csa()
        if not inq: return
        # se livello è none setta a 0
        if not inq['liv']: inq['liv'] = 0
        poseco_model = apps.get_model(app_label='gestione_risorse_umane',
                                      model_name='PosizioneEconomica')
        liv_poseco_model = apps.get_model(app_label='gestione_risorse_umane',
                                          model_name='LivelloPosizioneEconomica')
        pos_eco = poseco_model.objects.filter(nome=inq['cat']).first()
        if not pos_eco:
            pos_eco = poseco_model.objects.create(nome=inq['cat'],
                                                  descrizione=inq['descr'])
        csa_livello = liv_poseco_model.objects.filter(posizione_economica=pos_eco,
                                                      nome=inq['liv']).first()
        if not csa_livello:
            csa_livello = liv_poseco_model.objects.create(posizione_economica=pos_eco,
                                                          nome=inq['liv'])

        if not self.livello or self.livello != csa_livello:
            self.livello = csa_livello
            self.save()
        return csa_livello

    def get_data_presa_servizio_csa(self):
        if self.data_presa_servizio_manuale:
            return self.data_presa_servizio_manuale

        c = self.get_first_carriera_csa()
        # trovo la prima presa di servizio scartando le eventuali cessazioni
        v =  c['data_inizio']
        # v =  c[0][CARRIERA_FIELDS_MAP['data_inizio_rapporto']]
        if not v:
            raise CSAException(message='Il dipendente non ha una data di presa servizio in CSA!',
                               errors=['dt_rap_ini è vuoto',])
        return timezone.get_current_timezone().localize(v)

    def get_data_cessazione_servizio_csa(self):
        # TODO
        if self.data_cessazione_contratto_manuale:
            return self.data_cessazione_contratto_manuale
        # USO data_fine qui
        c = self.get_carriera_csa()
        if not c: return False
        v = c[0]['data_fine']
        # preleva il dt_fin più alto di numero
        for i in c:
            if i['data_fine'] > v:
                v = i['data_fine']
        return timezone.get_current_timezone().localize(v)

    def get_incarichi_csa(self):
        anagrafica_csa = self.get_anagrafica_csa()
        if not anagrafica_csa:
            return False
        return anagrafica_csa.get_incarichi_view()

    def sync_csa(self):
        """
        replica i dati da CSA e salva la data_ultima_sincronizzazione
        """
        c = self.get_carriera_csa()
        if not c: return False

        self.set_inquadramento_from_csa()
        self.sede = self.get_sede_csa()

        anagrafica = self.get_anagrafica_csa()
        self.nome = anagrafica.nome
        self.cognome = anagrafica.cognome
        # print(self.get_afforg_csa())
        # print(self.get_profilo_csa())
        afforg_model = apps.get_model(app_label='gestione_risorse_umane',
                                      model_name='AfferenzaOrganizzativa')
        afforg = afforg_model.objects.filter(nome=self.get_afforg_csa()).first()
        if not afforg and self.get_afforg_csa():
            afforg = afforg_model.objects.create(nome=self.get_afforg_csa())
        self.afferenza_organizzativa = afforg
        tipoprofilo_model = apps.get_model(app_label='gestione_risorse_umane',
                                           model_name='TipoProfiloProfessionale')
        profilo = tipoprofilo_model.objects.filter(nome=self.get_profilo_csa()).first()
        if not profilo:
            profilo = tipoprofilo_model.objects.create(nome=self.get_profilo_csa())
        self.profilo = profilo

        self.ruolo = self.get_ruolo_csa()
        self.data_presa_servizio = self.get_data_presa_servizio_csa()
        self.data_cessazione_contratto = self.get_data_cessazione_servizio_csa()
        self.data_ultima_sincronizzazione = timezone.localtime()
        self.save()
        return self.data_ultima_sincronizzazione
