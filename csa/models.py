from django.conf import settings
from django.core.cache import cache
from django.db import models
from collections import OrderedDict

RUOLI = [('ND', 'ND - Personale non docente'),
         ('DC', 'DC - Dirigente a contratto'),
         ('NB', 'NB - ND Centro Residenziale'),
         ('D0', 'D0 - Dirigenti Superiori'),
         ('NM', 'NM - Non docenti a tempo det.-Tesoro'),
         ('NG', 'NG - Addetti ufficio stampa'),
         ('PO', 'PO - Professori Ordinari'),
         ('PA', 'PA - Professori Associati'),
         ('RU', 'RU - Ricercatori Universitari'),
         ('RM', 'RM - Ricercatori a tempo det-Tesoro'),
         ('RD', 'RD - Ricercatori Legge 240/10 - t.det.')]

CARRIERA_FIELDS_MAP = {'descr_aff_org': 'ds_aff_org',
                       'descr_sede':    'ds_sede',
                       'descr_inquadramento': 'ds_inquadr',
                       'descr_profilo':       'ds_profilo',
                       'attivita':      'attivita',
                       'data_inizio_rapporto': 'dt_rap_ini',
                       'data_inizio':   'dt_ini',
                       'data_fine':     'dt_fin',
                       'inquadramento': 'inquadr',
                       'ruolo': 'ruolo'}

# per i docenti invence rimuoviamo gli attributi inutili e aggiungiamo quelli specifici
CARRIERA_DOCENTE_FIELDS_MAP = CARRIERA_FIELDS_MAP.copy()
del CARRIERA_DOCENTE_FIELDS_MAP['descr_profilo']
CARRIERA_DOCENTE_FIELDS_MAP.update({"aff_org": "aff_org",
                                    "ds_ruolo": "ds_ruolo",
                                    "ds_attivita": "ds_attivita",
                                    "dt_avanz" : "dt_avanz",
                                    "dt_prox_avanz" : "dt_prox_avanz",
                                    "cd_sett_concors" : "cd_sett_concors",
                                    "ds_sett_concors" : "ds_sett_concors",
                                    "cd_ssd" : "cd_ssd",
                                    "ds_ssd" : "ds_ssd",
                                    "area_ssd" : "area_ssd",
                                    "ds_area_ssd" : "ds_area_ssd",
                                    "scatti" : "scatti",
                                    "inquadramento": "inquadr",
                                    "descr_inquadramento": "ds_inquadr"})

INCARICHI_FIELDS_MAP = {'data_doc': 'data_doc',
                        'num_doc': 'num_doc',
                        'tipo_doc': 'tipo_doc',
                        'descr_tipo': 'des_tipo',
                        'data_inizio':   'dt_ini',
                        'data_fine':     'dt_fin',
                        'relaz_accomp': 'relaz_accomp',
                        'ruolo': 'ruolo'}


def _get_matricola(matricola):
    return matricola.zfill(6)


class V_ANAGRAFICA(models.Model):
    """
    Configurazione Oracle view
    gdm = V_ANAGRAFICA.objects.get(matricola='17403'.zfill(6))
    """
    nome = models.CharField(max_length=100, blank=True, null=True)
    cognome = models.CharField(max_length=100, blank=True, null=True)
    matricola = models.CharField(max_length=6, primary_key=True)
    email = models.EmailField(max_length=100, blank=True, null=True)
    cod_fis = models.CharField('Codice Fiscale', max_length=16, blank=False, null=False)

    class Meta:
        db_table = 'V_ANAGRAFICA'
        ordering = ['cognome',]
        # no database table creation or deletion operations will be performed for this model
        if settings.CSA_MODE == 'native':
            managed = False
        verbose_name = 'Anagrafica'
        verbose_name_plural = 'Anagrafiche'

    def get_carriera_view(self):
        cache_name = '{}_{}'.format(_get_matricola(self.matricola),
                                    'carriera_csa')
        csa_cache = cache.get(cache_name)
        if csa_cache: return csa_cache
        # per dipendenti
        q = 'SELECT * FROM V_CARRIERA where matricola={} ORDER BY {} DESC'.format(self.matricola,
                                                                                  CARRIERA_FIELDS_MAP['data_inizio'])
        carriere = V_ANAGRAFICA.objects.raw(q)
        c = []
        for carriera in carriere:
            d = OrderedDict()
            for field in CARRIERA_FIELDS_MAP:
                d[field] = getattr(carriera, CARRIERA_FIELDS_MAP[field])
            c.append(d)
        cache.set(cache_name, c)
        return c

    def get_carriera_docente_view(self):
        cache_name = '{}_{}'.format(_get_matricola(self.matricola),
                                    'carriera_docente_csa')
        csa_cache = cache.get(cache_name)
        if csa_cache: return csa_cache
        # per docenti
        q = 'SELECT * FROM V_CARRIERA_DOCENTI where matricola={} ORDER BY {} DESC'.format(self.matricola,
                                                                                          CARRIERA_DOCENTE_FIELDS_MAP['data_inizio'])
        carriere = V_ANAGRAFICA.objects.raw(q)
        c = []
        for carriera in carriere:
            d = OrderedDict()
            for field in CARRIERA_DOCENTE_FIELDS_MAP:
                d[field] = getattr(carriera, CARRIERA_DOCENTE_FIELDS_MAP[field])
            c.append(d)
        cache.set(cache_name, c)
        return c

    def get_incarichi_view(self):
        cache_name = '{}_{}'.format(_get_matricola(self.matricola), 'incarichi_csa')
        csa_cache = cache.get(cache_name)
        if csa_cache: return csa_cache
        q = 'SELECT * FROM V_INCARICO_DIP where matricola={} ORDER BY {} DESC'.format(self.matricola,
                                                                                      INCARICHI_FIELDS_MAP['data_inizio'])
        incarichi = V_ANAGRAFICA.objects.raw(q)
        c = []
        for incarico in incarichi:
            d = OrderedDict()
            for field in INCARICHI_FIELDS_MAP:
                d[field] = getattr(incarico, INCARICHI_FIELDS_MAP[field])
            c.append(d)
        cache.set(cache_name, c)
        return c

    def __str__(self):
        return '{} - {} {}'.format(self.matricola, self.nome, self.cognome)


class V_RUOLO(models.Model):
    """
    Configurazione Oracle view
    """
    ruolo = models.CharField(max_length=4, primary_key=True)
    comparto = models.CharField(max_length=1, blank=True, null=True)
    tipo_ruolo = models.CharField(max_length=2, blank=False, null=False)
    descr = models.CharField(max_length=254, blank=True, null=True)
    is_docente = models.NullBooleanField(default=False)

    class Meta:
        db_table = 'V_RUOLO'
        # no database table creation or deletion operations will be performed for this model
        if settings.CSA_MODE == 'native':
            managed = False
        verbose_name = 'Ruolo'
        verbose_name_plural = 'Ruoli'

    def __str__(self):
        return '{} - {} {}'.format(self.ruolo, self.tipo_ruolo, self.descr)


# niente da fare, non ho chiavi primarie dalle viste in 'native' mode.
# mentre in replica posso sfruttarle
if settings.CSA_MODE == 'replica':
    class V_CARRIERA(models.Model):
        """
        Configurazione Oracle view
        """
        matricola = models.CharField(max_length=6)
        ds_aff_org = models.CharField(max_length=254, blank=True, null=True)
        ds_sede = models.CharField(max_length=254, blank=True, null=True)
        ds_inquadr = models.CharField(max_length=254, blank=True, null=True)
        ds_profilo = models.CharField(max_length=254, blank=True, null=True)
        ruolo = models.CharField(max_length=254, blank=True, null=True)
        inquadr = models.CharField(max_length=254, blank=True, null=True)
        dt_ini = models.DateTimeField(blank=True, null=True)
        dt_fin = models.DateTimeField(blank=True, null=True)
        dt_rap_ini = models.DateTimeField(blank=True, null=True)
        attivita = models.CharField(max_length=254, blank=True, null=True)
        class Meta:
            db_table = 'V_CARRIERA'
            verbose_name = 'Carriera'
            verbose_name_plural = 'Carriere'

        def __str__(self):
            return '{} - {} {}'.format(self.matricola,
                                       self.ruolo, self.dt_ini)


    class V_CARRIERA_DOCENTI(models.Model):
        """
        Mappatura su Oracle view
        """
        matricola = models.CharField(max_length=6)
        ds_aff_org = models.CharField(max_length=254, blank=True, null=True)
        ds_sede = models.CharField(max_length=254, blank=True, null=True)
        ds_inquadr = models.CharField(max_length=254, blank=True, null=True)
        ruolo = models.CharField(max_length=254, blank=True, null=True)
        inquadr = models.CharField(max_length=254, blank=True, null=True)
        dt_ini = models.DateTimeField(blank=True, null=True)
        dt_fin = models.DateTimeField(blank=True, null=True)
        dt_rap_ini = models.DateTimeField(blank=True, null=True)
        attivita = models.CharField(max_length=254, blank=True, null=True)

        #tipici dei docenti
        aff_org = models.CharField(max_length=254, blank=True, null=True)
        ds_attivita = models.CharField(max_length=254, blank=True, null=True)
        ds_ruolo = models.CharField(max_length=254, blank=True, null=True)
        dt_avanz = models.DateField(blank=True, null=True)
        dt_prox_avanz = models.DateField(blank=True, null=True)
        cd_sett_concors = models.CharField(max_length=10, blank=True, null=True)
        ds_sett_concors = models.CharField(max_length=254, blank=True, null=True)
        cd_ssd = models.CharField(max_length=12, blank=True, null=True)
        ds_ssd = models.CharField(max_length=100, blank=True, null=True)
        area_ssd = models.CharField(max_length=2, blank=True, null=True)
        ds_area_ssd = models.CharField(max_length=100, blank=True, null=True)
        scatti = models.BooleanField(default=0)

        class Meta:
            db_table = 'V_CARRIERA_DOCENTI'
            verbose_name = 'Carriera Docente'
            verbose_name_plural = 'Carriere Docenti'

        def __str__(self):
            return '{} - {} {}'.format(self.matricola,
                                       self.ruolo, self.dt_ini)


    class V_INCARICO_DIP(models.Model):
        """
        Configurazione Oracle view per incarichi
        """
        matricola = models.CharField(max_length=6)
        ruolo = models.CharField(max_length=254, blank=True, null=True)
        relaz_accomp = models.CharField(max_length=1024, blank=True, null=True)
        des_tipo = models.CharField(max_length=254, blank=True, null=True)
        tipo_doc = models.CharField(max_length=254, blank=True, null=True)
        num_doc = models.CharField(max_length=254, blank=True, null=True)
        data_doc = models.DateTimeField(blank=True, null=True)
        dt_ini = models.DateTimeField(blank=True, null=True)
        dt_fin = models.DateTimeField(blank=True, null=True)

        class Meta:
            db_table = 'V_INCARICO_DIP'
            verbose_name = 'Incarichi'
            verbose_name_plural = 'Incarichi'

        def __str__(self):
            return '{} - {} {}'.format(self.matricola,
                                       self.ruolo, self.dt_ini)
