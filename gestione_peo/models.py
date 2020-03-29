import inspect
import operator
import sys


from django.apps import apps
from django.conf import settings
from django.core.validators import EMPTY_VALUES
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django_form_builder.dynamic_fields import format_field_name, get_fields_types
from django_form_builder.models import DynamicFieldMap
from gestione_risorse_umane.models import (PosizioneEconomica,
                                           TitoloStudio)
from model_utils.fields import AutoCreatedField, AutoLastModifiedField
from unical_template.models import TimeStampedModel, CreatedModifiedModel
from unical_template.utils import text_as_html #differenza_date_in_mesi_aru non più chiamato

from . import peo_formfields
# per la prima volta vedo un forms importato nel models (solitamente era il contrario!)
from .forms import PeoDynamicForm
from .settings import (ETICHETTA_INSERIMENTI_ID,
                       ETICHETTA_INSERIMENTI_LABEL,
                       ETICHETTA_INSERIMENTI_HELP_TEXT)

if 'csa' in settings.INSTALLED_APPS:
    from csa.models import RUOLI
else:
    RUOLI = settings.RUOLI

_UNITA_TEMPORALI = (('h', _('ore')),
                    ('d', _('giorni')),
                    ('m', _('mesi')),
                    ('y', _('anni')))

_UNITA_TEMPORALI_INT_MAP = {'y': 12, # anni in mesi
                            'm': 1, # mesi in mesi
                            'g': 1, # giorni in giorni
                            'h': 1} # ore in ore

_MATH_OPERATOR_FUNC_MAP = {'x': operator.mul,
                           '+': operator.add,
                           '-': operator.sub,
                           '/': operator.truediv,
                           'a': None} # assegna il valore così com'è, senza operazione

_OPERATORI_PUNTEGGIO = (('x', _('moltiplicatore')),
                        ('a', _('assegnazione')),
                        # inutilizzati, creati per opportuna generalizzazione
                        ('+', _('addizione')),
                        ('/', _('divisione')),
                        ('-', _('sottrazione')))


class Bando(TimeStampedModel):
    """
    Configurazione di una Sessione PEO
    """
    nome = models.CharField(max_length=255, blank=False, null=False,
                            help_text="Procedura Elettronica On-line A.A.2017")
    slug = models.CharField(max_length=255, blank=False, null=False, unique=True)
    data_inizio = models.DateTimeField()
    data_fine   = models.DateTimeField()
    data_fine_presentazione_domande = models.DateTimeField()
    descrizione = models.TextField(blank=True, default='')
    ultima_progressione = models.DateField(help_text=("Data dell'ultima"
                                                      " progressione per"
                                                      " poter partecipare"
                                                      " alla sessione"))
    anni_servizio_minimi = models.IntegerField("Anni di servizio minimi",
                                               default = 3,
                                               help_text=("Anni di servizio minimi"
                                                          " per poter partecipare"
                                                          " al bando"))
    data_validita_titoli_fine = models.DateField("Data fine validità titoli",
                                                 help_text=("Data fino alla quale"
                                                            " i titoli sono accettati"))
    agevolazione_soglia_anni = models.IntegerField( "Anni permanenza per bonus"
                                                    " punteggio anzianità",
                                                    default=3,
                                                    help_text=("Anzianità di servizio"
                                                        " nella stessa posizione economica"
                                                        " per usufruire della moltiplicazione"
                                                        " del punteggio relativo all'anzianità"
                                                        " di servizio"))
    agevolazione_fatmol = models.IntegerField( "Fattore moltiplicazione per bonus"
                                               " punteggio anzianità",
                                               default=3,
                                               help_text=("Fattore di moltiplicazione"
                                                          " del punteggio relativo all'anzianità"
                                                          " di servizio nel caso di permanenza"
                                                          " maggiore o uguale alla soglia stabilita."
                                                          "Serve per agevolare i dipendenti che da N anni"
                                                          " non superano la progressione"))
    priorita_titoli_studio = models.BooleanField("Valuta solo titolo di studio"
                                                 " più elevato",
                                                 default=True,
                                                 help_text=("Se attivo, nel calcolo del punteggio,"
                                                            " verrà valutata solo"
                                                            " la categoria di titoli"
                                                            " di studio più elevata."
                                                            " (Es: laurea magistrale > laurea triennale)"))
    bando_url = models.URLField(max_length=255, blank=True, null=True,
                          help_text="URL della risorsa web con le specifiche del Bando")
    redazione = models.BooleanField(default=False,
                                    help_text=("Se attivo sarà di riferimento per"
                                               " la valutazione delle idoneità AD USO INTERNO:"
                                               " azioni e filtri backend."))
    collaudo = models.BooleanField(default=False,
                                   help_text="Se selezionato sarà visibile ai soli utenti afferenti al gruppo STAFF")
    pubblicato = models.BooleanField(default=False,
                                     help_text="Se selezionato sarà visibile al pubblico")
    email_avvenuto_completamento = models.BooleanField(default=False,
                                                       help_text=("Se selezionato verrà inviata una email "
                                                                  "di avvenuta trasmissione della domanda"))
    pubblica_punteggio = models.BooleanField(default=False,
                                             help_text="Rende visibile il "
                                                       "punteggio calcolato "
                                                       "agli utenti")
    # attributi per la classificazione/protocollazione
    protocollo_required = models.BooleanField("Protocollo domanda obbligatorio",
                                      default=False,
                                      help_text=("Se attivo la domanda di partecipazione al bando"
                                                 " dovrà necessariamente essere protocollata in fase"
                                                 " di chiusura"))
    protocollo_cod_titolario = models.CharField('Codice titolario',
                                                max_length=12,
                                                choices=settings.PROTOCOLLO_CODICI_TITOLARI,
                                                null=True, blank=True)
    protocollo_fascicolo_numero = models.CharField('Fascicolo numero',
                                                   max_length=12,
                                                   null=False, blank=False,
                                                   default=settings.PROTOCOLLO_FASCICOLO_DEFAULT)
    protocollo_template = models.TextField(help_text=("Template XML che "
                                                      "descrive il flusso"),
                                           blank=True, default='')
    accettazione_clausole_text = models.TextField('Testo Accettazione Clausole',
                                                  help_text=("es. Dichiaro di aver preso visione..."),
                                                  blank=True, null=True)
    class Meta:
        verbose_name = _('Bando')
        verbose_name_plural = _('Bandi')

    def __str__(self):
        return '{}'.format(self.nome)

    def descr_as_html(self):
        return text_as_html(self.descrizione)

    def non_ancora_iniziato(self):
        return timezone.localtime() < self.data_inizio

    def is_scaduto(self):
        return timezone.localtime() > self.data_fine

    def is_in_corso(self):
        return timezone.localtime() >= self.data_inizio and \
               timezone.localtime() <= self.data_fine

    def presentazione_domande_scaduta(self):
        return timezone.localtime() > self.data_fine_presentazione_domande

    def indicatore_con_anzianita(self):
        """
        restituisce l'indicatore ponderato al cui punteggio si somma quello
        relativo all'anzianità interna.
        senza questo indicatore, l'anzianità non viene presa in considerazione
        nel calcolo del punteggio
        """
        indicatore_anzianita = self.indicatoreponderato_set.filter(add_punteggio_anzianita=True).first()
        if indicatore_anzianita:
            return "({}) {}".format(indicatore_anzianita.id_code,
                                    indicatore_anzianita.nome)
        return False

    def get_punteggio_titoli_pos_eco(self, livello_pos_eco):
        """
        torna la lista dei titoli configurati con punteggio (abilitati)
        escludendo i titoli disabilitati per livello_pos_eco

        examples
        from gestione_risorse_umane.models import *
        from gestione_peo.models import *
        bando = Bando.objects.all()[1]
        livello_pos_eco = LivelloPosizioneEconomica.objects.get(posizione_economica__nome='C', nome=1)
        bando.get_titoli_pos_eco(livello_pos_eco)

        """
        excluded_cat = self.categoriedisabilitate_titolostudio_set.filter(posizione_economica=livello_pos_eco)
        excluded_titoli = [i.titolo_studio.pk for i in excluded_cat]
        punteggi_titoli = self.punteggio_titolostudio_set.exclude(titolo__pk__in=excluded_titoli)
        return punteggi_titoli

    def get_titoli_pos_eco(self, livello_pos_eco):
        punteggi_titoli = get_punteggio_titoli_pos_eco(livello_pos_eco)
        if punteggi_titoli:
            return TitoloStudio.objects.filter(pk__in=[i.titolo.pk for i in punteggi_titoli])


class IndicatorePonderato(TimeStampedModel):
    """
    Creando una nuova sessione in automatico vengono riprodotte
    tutte le categorie della Sessione precedente.
    L'operatore può a valle rimuoverne o aggiungerne di nuove
    """
    bando = models.ForeignKey(Bando, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255, blank=False, null=False,
                            help_text="Indicatore Ponderato (art.82 CCNL)")
    id_code = models.CharField('Codice identificativo', max_length=33, blank=False,
                               null=False,
                               help_text='Lettera, numero o sequenza')
    note = models.TextField(help_text=("es. Solo ai candidati in possesso"
                                       " di un'anzianità di servizio di almeno 3 anni..."),
                            blank=True, default='')
    add_punteggio_anzianita = models.BooleanField("Somma Punteggio Anzianità Servizio",
                                                  default=False,
                                                  help_text=("Se attivo, al punteggio derivante dagli inserimenti"
                                                             " del Dipendente, verrà sommato il punteggio relativo"
                                                             " all'anzianità di servizio (Unical), rispettando"
                                                             " sempre il max ottenibile"))

    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        unique_together = ('bando', 'id_code' )
        verbose_name = _('Indicatore Ponderato')
        verbose_name_plural = _('Indicatori Ponderati')
        ordering = ['bando','nome',]

    def get_pmax_pos_eco(self, categoria_economica):
        """
        Ritorna PunteggioMaxIndicatore per PosizioneEconomica
        prendendo come parametro la categoria_economica
        """
        punteggio_max = 0
        if self.punteggiomax_indicatoreponderato_poseconomica_set.first():
            for punteggio_ind in self.punteggiomax_indicatoreponderato_poseconomica_set.all():
                if punteggio_ind.posizione_economica == categoria_economica:
                    return punteggio_ind.punteggio_max
                elif not punteggio_ind.posizione_economica:
                    punteggio_max_indicatore = punteggio_ind_cat.punteggio_max
        return punteggio_max

    def __str__(self):
        return '{} - {}'.format(self.nome, self.bando)


class PunteggioMax_IndicatorePonderato_PosEconomica(models.Model):
    """
    Questa classe definisce il punteggio massimo che può essere attribuito
    a un istante, appartenente a una determinata posizione economica, per
    una specifica Categoria di Titoli (Indicatori Ponderati)
    """
    indicatore_ponderato = models.ForeignKey(IndicatorePonderato,
                                             on_delete=models.CASCADE)
    posizione_economica = models.ForeignKey(PosizioneEconomica,
                                            on_delete=models.CASCADE,
	                                        verbose_name='Categoria')
    punteggio_max = models.PositiveIntegerField(help_text="es. EP 20, D 20, C 20, B 25")
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        verbose_name = _('Punteggio Max Indicatore Ponderato per Categoria')
        verbose_name_plural = _('Punteggi Max Indicatore Ponderato per Categorie')


class DescrizioneIndicatore(TimeStampedModel):
    indicatore_ponderato = models.ForeignKey(IndicatorePonderato,
                                             on_delete=models.CASCADE)
    nome = models.CharField(max_length=255, blank=False, null=False,
                            help_text="Descrizione degli indicatori")
    id_code = models.CharField('Codice identificativo',
                               max_length=33, blank=False,
                               null=False, help_text='Lettera, numero o sequenza')
    calcolo_punteggio_automatico = models.BooleanField(default=False,
                                                       help_text=("Se disabilitato richiede valutazione manuale"
                                                                  " e non richiede la definizione di indicatori di"
                                                                  " valutazione o pesi/punteggi a sistema"))
    non_cancellabile = models.BooleanField("Impossibile eliminare i moduli compilati nella domanda",
                                           default=False,
                                           help_text=("Se attivo, dalla domanda non potranno essere"
                                                      " eliminati i relativi moduli compilati e"
                                                      " l'intera domanda non potrà essere distrutta"
                                                      ))
    limite_inserimenti = models.BooleanField("Limita numero inserimenti",
                                             default=False,
                                             help_text=("Se attivo, specificare il numero"
                                                        " di inserimenti permessi"))
    numero_inserimenti = models.IntegerField("Numero max inserimenti",
                                             default=1,
                                             validators=[MinValueValidator(1),],
                                             help_text=("Numero max inserimenti consentiti"))
    is_required = models.BooleanField("Inserimento in domanda obbligatorio",
                                      default=False,
                                      help_text=("Se attivo la domanda non potrà essere presentata senza la presenza"
                                                 " di questo Indicatore."
                                                ))
    note = models.TextField(help_text=("es. Non saranno oggetto di valutazione "
                                       "di sorveglienza/vigilanza antifumo..."),
                            blank=True, default='')
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        verbose_name = _('Descrizione Indicatore')
        verbose_name_plural = _('Descrizioni Indicatori')
        ordering = ['indicatore_ponderato', 'ordinamento',]

    def get_pmax_pos_eco(self, categoria_economica):
        """
        Ritorna PunteggioMaxDescrizioneIndicatore per PosizioneEconomica
        prendendo come parametro la categoria_economica
        """
        punteggio_max = 0
        if self.punteggiomax_descrizioneindicatore_poseconomica_set.first():
            for punteggio_descr in self.punteggiomax_descrizioneindicatore_poseconomica_set.all():
                if punteggio_descr.posizione_economica == categoria_economica:
                    return punteggio_descr.punteggio_max
                elif not punteggio_descr.posizione_economica:
                    punteggio_max = punteggio_descr.punteggio_max
        return punteggio_max

    def get_fields_order(self):
        """
        Ritorna l'ordinamento dei fields che compongono il form associato,
        definito da backend
        """
        fields_order = [ETICHETTA_INSERIMENTI_ID,]
        for i in self.moduloinserimentocampi_set.all():
            appended = False
            class_name=sys.modules['gestione_peo.peo_formfields']
            for m in inspect.getmembers(class_name, inspect.isclass):
                is_complex = False
                if hasattr(m[1], 'is_complex'):
                    is_complex=getattr(m[1], 'is_complex')
                to_check = is_complex or hasattr(m[1], 'name')
                if m[0]==i.field_type and to_check:
                    dyn_field=m[1]()
                    if is_complex:
                        fields = dyn_field.get_fields()
                        for f in fields:
                            if hasattr(f, 'name'):
                                fields_order.append(f.name)
                    else: fields_order.append(dyn_field.name)
                    appended=True
                if appended: break
            if not appended:
                fields_order.append(format_field_name(i.name))
        return fields_order

    def get_form(self,
                 data=None,
                 files=None,
                 remove_filefields=False,
                 remove_datafields=False,
                 force_sorting=True,
                 **kwargs):
        """
        files solitamente request.FILES vedi domande_peo.views.aggiungi_titolo
        """
        moduli_inserimento = self.moduloinserimentocampi_set.all()
        if not moduli_inserimento: return None

        # Static method of DynamicFieldMap
        constructor_dict = DynamicFieldMap.build_constructor_dict(moduli_inserimento)
        custom_params = {'domanda_bando': kwargs.get('domanda_bando'),
                         'descrizione_indicatore': self}

        fields_order=self.get_fields_order() if force_sorting else []
        form = DynamicFieldMap.get_form(PeoDynamicForm,
                                        constructor_dict=constructor_dict,
                                        custom_params=custom_params,
                                        data=data,
                                        files=files,
                                        remove_filefields=remove_filefields,
                                        remove_datafields=remove_datafields,
                                        fields_order=fields_order)
        return form

    def is_available_for_cateco(self, cateco):
        """
        cateco is PosizioneEconomica object
        ritorna vero se questo descr_ind è abilitato per la categoria del dipendente
        """
        catdis = CategorieDisabilitate_DescrizioneIndicatore.objects.filter(descrizione_indicatore=self).first()
        if not catdis: return True
        if cateco not in catdis.posizione_economica.all():
            return True

    def is_available_for_ruolo(self, ruolo):
        """
        ritorna vero se questo descr_ind è abilitato per il ruolo del dipendente
        """
        ruolidis = RuoliDisabilitati_DescrizioneIndicatore.objects.filter(descrizione_indicatore=self).all()
        if not ruolidis: return True
        for ruolodis in ruolidis:
            if ruolo == ruolodis.ruolo:
                return False
        return True

    def is_available_for_cat_role(self, cateco, ruolo):
        """
        ritorna vero se questo descr_ind è abilitato
        sia per il ruolo che per la categoria economica del dipendente
        """
        available_cateco = self.is_available_for_cateco(cateco)
        available_ruolo = self.is_available_for_ruolo(ruolo)
        return available_cateco and available_ruolo

    def note_as_html(self):
        return text_as_html(self.note)

    def __str__(self):
        return '{} ({})'.format(self.nome,
                                     self.indicatore_ponderato,)


class PunteggioMax_DescrizioneIndicatore_PosEconomica(models.Model):
    """
    Questa classe definisce il punteggio massimo che può essere attribuito
    a un istante, appartenente a una determinata posizione economica, per
    uno specifico Indicatore di Titoli (Sottocategoria degli Indicatori Ponderati)
    """
    descrizione_indicatore = models.ForeignKey(DescrizioneIndicatore,
	                                      on_delete=models.CASCADE,
	                                      verbose_name='Indicatore titolo')
    posizione_economica = models.ForeignKey(PosizioneEconomica,
	                                        verbose_name='Categoria',
                                            on_delete=models.CASCADE)
    punteggio_max = models.FloatField(help_text="es. max 10 punti per ctg EP-D-C, max 12 punti per ctg B")
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        verbose_name = _('Punteggio Max Descrizione Indicatore per Categoria')
        verbose_name_plural = _('Punteggi Max Descrizione Indicatore per Categoria')


class Punteggio_DescrizioneIndicatore(models.Model):
    descrizione_indicatore = models.ForeignKey(DescrizioneIndicatore,
                                               on_delete=models.CASCADE,
                                               verbose_name='Descrizione Indicatore')
    nome = models.CharField(max_length=255,
                            blank=False, null=False,
                            default="")
    pos_eco = models.ForeignKey(PosizioneEconomica,
                                on_delete=models.CASCADE,
                                verbose_name='Categoria',
                                blank=True, null=True
                                )
    punteggio = models.FloatField()
    note = models.CharField(max_length=255, blank=True,
                            help_text="Descrizione",
                            default="")
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        verbose_name = _('Punteggio per Categoria')
        verbose_name_plural = _('Punteggi per Categoria')

    def __str__(self):
        return '{}, {}: {}'.format(self.descrizione_indicatore,
                                   self.pos_eco,
                                   self.punteggio)


class Punteggio_DescrizioneIndicatore_TimeDelta(models.Model):
    """
    Questa classe rappresenta particolari categorie di titoli il cui
    punteggio viene assegnato in base alla durata temporale del contestuale
    corso seguito
    """

    descrizione_indicatore = models.ForeignKey(DescrizioneIndicatore,
                                               on_delete=models.CASCADE,
                                               verbose_name='Descrizione Indicatore')
    nome = models.CharField(max_length=255, blank=False, null=False,
                            help_text=("Descrizione degli indicatori"
                                       "nome del titolo presentato"),
                            default="")
    pos_eco = models.ForeignKey(PosizioneEconomica,
                                on_delete=models.CASCADE,
                                verbose_name='Categoria',
                                blank=True, null=True
                                )
    unita_temporale = models.CharField('Unita temporale di riferimento',
                                       max_length=1, choices=_UNITA_TEMPORALI,
                                       default="m")
    durata_minima = models.PositiveIntegerField(help_text="quantità riferita all'unità temporale di riferimento")
    durata_massima = models.PositiveIntegerField(help_text="es. 'oltre 16 ore' immettere 17 ore")
    # punteggio_max = models.PositiveIntegerField(help_text="es. max 10 punti per ctg EP-D-C, max 12 punti per ctg B")
    punteggio = models.FloatField(help_text="In base all'operatore selezionato"
                                            " viene assegnato all'intervallo temporale"
                                            " o a singole ore/mesi/anni dell'intervallo")
    operatore = models.CharField('Operatore da applicare al punteggio',
                                 help_text="Operatore che determina l'assegnazione",
                                 max_length=1, choices=_OPERATORI_PUNTEGGIO,
                                 default="a")

    note = models.CharField(max_length=255, blank=True,
                            help_text="Descrizione",
                            default="")
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        # unique_together = ('ind_tit', 'nome', 'pos_eco')
        verbose_name = _('Punteggio per durata temporale')
        verbose_name_plural = _('Punteggi per durata temporale')

    def get_intero_unita_temporale(self):
        """
        in base al valore d,m,y torna l'interno relativo

        # per discretizzazioni mesi/giorni implementare metodi
        specializzati con import calendar
        """
        return _UNITA_TEMPORALI_INT_MAP[self.unita_temporale]

    def get_operator_function(self):
        """
        in base al simbolo torna la funzione mappata in
        _MATH_OPERATOR_FUNC_MAP (import operator)
        """
        return _MATH_OPERATOR_FUNC_MAP[self.operatore]

    def check_corrispondenza_intervallo(self, cat_eco=None,intervallo=0):
        """
        Controlla se l'intervallo passato come argomento ricade nei
        limiti durata_minima e durata_massima del timedelta.
        Se l'argomento 'cat_eco' è settato, lo confronta con il self.pos_eco
        """
        if not intervallo: return False
        if cat_eco and cat_eco != self.pos_eco: return False
        return intervallo >= self.durata_minima and intervallo <= self.durata_massima

    def calcola_punteggio(self, durata):
        """
        durata è il secondo argomento del calcolo
        se invece è una assegnazione torna punteggio
        """
        if not self.get_operator_function():
            # se la funzione è nulla torna il punteggio
            return self.punteggio

        funzione_calcolo = self.get_operator_function()
        return funzione_calcolo(self.punteggio, durata)

    def __str__(self):
        if self.pos_eco:
            return '{}, {}: {}'.format(self.descrizione_indicatore,
                                       self.pos_eco,
                                       self.punteggio)
        return '{}: {}'.format(self.descrizione_indicatore,
                               self.punteggio)


class Punteggio_TitoloStudio(TimeStampedModel):
    titolo = models.ForeignKey(TitoloStudio,
                               on_delete=models.CASCADE,
                               blank=False, null=False, default=1)
    bando = models.ForeignKey(Bando, on_delete=models.CASCADE,
                              blank=False, null=False, default=1)
    punteggio = models.PositiveIntegerField()
    cumulabile = models.BooleanField(default=False,
                                     help_text=("Indica se più titoli equivalenti"
                                                " possano essere cumulati in una "
                                                "unica progressione"))
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        verbose_name = _('Punteggio per Titolo di Studio')
        verbose_name_plural = _('Punteggi per Titolo di Studio')

    def __str__(self):
        return '{} - punti {}'.format(self.titolo,
                              self.punteggio)


class Punteggio_Anzianita_Servizio(TimeStampedModel):
    """
    qui docstring :)
    """
    bando = models.ForeignKey(Bando, on_delete=models.CASCADE,
                              blank=False, null=False, default=1)
    posizione_economica = models.ForeignKey(PosizioneEconomica,
	                                        verbose_name='Categoria',
                                            on_delete=models.CASCADE)
    unita_temporale = models.CharField('Unita temporale di riferimento',
                                       max_length=1, choices=_UNITA_TEMPORALI,
                                       default="m")
    # Valore min. 0.0.1 perchè se l'anzianità viene valutata in base
    # ai mesi (anni in 12min) allora i punteggi sono frazioni di quelli
    # definiti nel bando (che sono assegnati agli anni)
    punteggio = models.FloatField(help_text=("punteggio attribuito per ogni anno/mese"
                                             " di servizio. Deve essere un numero"
                                             " positivo moltiplicabile per la "
                                             " durata dichiarata dall'utente istante"),
                                  validators = [MinValueValidator(0.01),])
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        verbose_name = _('Punteggio per Anzianità di servizio')
        verbose_name_plural = _('Punteggi per Anzianità di servizio')

    def __str__(self):
        return '{} - {} ogni {}'.format(self.posizione_economica,
                                        self.punteggio, self.unita_temporale)


class CategorieDisabilitate_TitoloStudio(models.Model):
    """
    Questa classe rappresenta per quali categorie economiche
    alcuni titoli di studio non sono valutati, in quanto considerati
    requisito di base
    """

    titolo_studio = models.ForeignKey(TitoloStudio,
                                      on_delete=models.CASCADE)
    bando = models.ForeignKey(Bando, on_delete=models.CASCADE,
                              blank=False, null=False, default=1)
    posizione_economica = models.ManyToManyField(PosizioneEconomica, blank=True)
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento", blank=True, default=0)

    class Meta:
        verbose_name = _('Categoria Disabilitata Punteggio Titolo Studio')
        verbose_name_plural = _('Categorie Disabilitate Punteggio Titolo Studio')

    def __str__(self):
        return '{} - {}'.format(self.bando, self.titolo_studio)


class ModuloInserimentoCampi(DynamicFieldMap):
    """
    Classe per la generazione dinamica di forms di inserimento relativi
    ai titoli (descrizione indicatori ponderati) dei dipendenti
    """
    descrizione_indicatore = models.ForeignKey(DescrizioneIndicatore,
                                               on_delete=models.CASCADE)
    DynamicFieldMap._meta.get_field('field_type').choices = get_fields_types(peo_formfields)

    class Meta:
        ordering = ('ordinamento', )
        verbose_name = _('Modulo di inserimento')
        verbose_name_plural = _('Moduli di inserimento')


class AvvisoBando(TimeStampedModel):
    """
    """
    bando = models.ForeignKey(Bando, on_delete=models.CASCADE)
    titolo = models.CharField(max_length=255, blank=False, null=False,
                              help_text="Titolo clausola (es: Privacy...)")
    corpo_del_testo = models.TextField(help_text=("es. Avviso riguardante..."),
                                       blank=False, null=False)
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)
    allegato = models.FileField(upload_to='avvisi_bando/%m-%Y/',
                                null=True,blank=True)
    is_active = models.BooleanField('Visibile agli utenti', default=True)

    class Meta:
        ordering = ('ordinamento', )
        verbose_name = _('Avviso Bando')
        verbose_name_plural = _('Avvisi Bando')

    def __str__(self):
        return '({}) {}'.format(self.bando, self.titolo)


class ClausoleBando(TimeStampedModel):
    """
    Crea le clausole del bando che ogni dipendete deve accettare prima
    di ogni domanda di partecipazione
    """
    bando = models.ForeignKey(Bando, on_delete=models.CASCADE)
    titolo = models.CharField(max_length=255, blank=False, null=False,
                              help_text="Titolo clausola (es: Privacy...)")
    corpo_del_testo = models.TextField(help_text=("es. La partecipazione al Bando comporta..."),
                                       blank=False, null=False)
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)
    allegato = models.FileField(upload_to='allegati_clausola_partecipazione/%m-%Y/',
                                null=True,blank=True)
    is_active = models.BooleanField('Visibile agli utenti', default=True)

    class Meta:
        ordering = ('ordinamento', )
        verbose_name = _('Clausola Bando')
        verbose_name_plural = _('Clausole Bando')

    def corpo_as_html(self):
        return text_as_html(self.corpo_del_testo)

    def __str__(self):
        return '({}) {}'.format(self.bando, self.titolo)


class SubDescrizioneIndicatore(TimeStampedModel):
    """
    """
    descrizione_indicatore = models.ForeignKey(DescrizioneIndicatore,
                                               on_delete=models.CASCADE)
    nome = models.CharField(max_length=255, blank=False, null=False,
                            help_text="Sotto-livello Descrizione degli indicatori")
    id_code = models.CharField('Codice identificativo',
                               max_length=33, blank=False,
                               null=False, help_text='Lettera, numero o sequenza')
    note = models.TextField(help_text=("es. Non saranno oggetto di valutazione "
                                       "di sorveglienza/vigilanza antifumo..."),
                            blank=True, default='')
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)

    class Meta:
        verbose_name = _('Sotto-livello Descrizione Indicatore')
        verbose_name_plural = _('Sotto-livelli Descrizione Indicatore')
        ordering = ['descrizione_indicatore', 'ordinamento',]

    def get_pmax_pos_eco(self, categoria_economica):
        """
        Ritorna PunteggioMaxDescrizioneIndicatore per PosizioneEconomica
        prendendo come parametro la categoria_economica
        """
        punteggio_max = 0
        if self.punteggiomax_subdescrizioneindicatore_poseconomica_set.first():
            for punteggio_subdescr in self.punteggiomax_subdescrizioneindicatore_poseconomica_set.all():
                if punteggio_subdescr.posizione_economica == categoria_economica:
                    return punteggio_subdescr.punteggio_max
                elif not punteggio_subdescr.posizione_economica:
                    punteggio_max = punteggio_subdescr.punteggio_max
        return punteggio_max

    def __str__(self):
        return '{}'.format(self.nome)


class PunteggioMax_SubDescrizioneIndicatore_PosEconomica(models.Model):
    """
    Questa classe definisce il punteggio massimo che può essere attribuito
    a un istante, appartenente a una determinata posizione economica, per
    uno specifico Indicatore di Titoli (Sottocategoria degli Indicatori Ponderati)
    """
    sub_descrizione_indicatore = models.ForeignKey(SubDescrizioneIndicatore,
	                                               on_delete=models.CASCADE,
	                                               verbose_name='Sub Descrizione Indicatore titolo')
    posizione_economica = models.ForeignKey(PosizioneEconomica,
	                                        verbose_name='Categoria',
                                            on_delete=models.CASCADE)
    punteggio_max = models.FloatField(help_text="es. max 10 punti per ctg EP-D-C, max 12 punti per ctg B")
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)

    class Meta:
        verbose_name = _('Punteggio Max Sub Descrizione Indicatore per Categoria')
        verbose_name_plural = _('Punteggi Max Sub Descrizione Indicatore per Categoria')


class Punteggio_SubDescrizioneIndicatore(models.Model):
    sub_descrizione_indicatore = models.ForeignKey(SubDescrizioneIndicatore,
                                                   on_delete=models.CASCADE,
                                                   verbose_name='Sub Descrizione Indicatore')
    nome = models.CharField(max_length=255,
                            blank=False, null=False,
                            default="")
    pos_eco = models.ForeignKey(PosizioneEconomica,
                                on_delete=models.CASCADE,
                                verbose_name='Categoria',
                                blank=True, null=True)
    punteggio = models.FloatField()
    note = models.CharField(max_length=255, blank=True,
                            help_text="Descrizione",
                            default="")
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)

    class Meta:
        # unique_together = ('ind_tit', 'nome', 'pos_eco')
        verbose_name = _('Punteggio per Categoria')
        verbose_name_plural = _('Punteggi per Categoria')

    def __str__(self):
        return '{}, {}: {}'.format(self.sub_descrizione_indicatore,
                                   self.pos_eco,
                                   self.punteggio)


class Punteggio_SubDescrizioneIndicatore_TimeDelta(models.Model):
    """
    Questa classe rappresenta particolari categorie di titoli il cui
    punteggio viene assegnato in base alla durata temporale del contestuale
    corso seguito
    """

    sub_descrizione_indicatore = models.ForeignKey(SubDescrizioneIndicatore,
                                                   on_delete=models.CASCADE,
                                                   verbose_name='Sub Descrizione Indicatore')
    nome = models.CharField(max_length=255, blank=False, null=False,
                            default="")
    pos_eco = models.ForeignKey(PosizioneEconomica,
                                on_delete=models.CASCADE,
                                verbose_name='Categoria',
                                blank=True, null=True)
    unita_temporale = models.CharField('Unita temporale di riferimento',
                                       max_length=1, choices=_UNITA_TEMPORALI,
                                       default="m")
    durata_minima = models.PositiveIntegerField(help_text="quantità riferita all'unità temporale di riferimento")
    durata_massima = models.PositiveIntegerField(help_text="es. 'oltre 16 ore' immettere 17 ore")
    # punteggio_max = models.PositiveIntegerField(help_text="es. max 10 punti per ctg EP-D-C, max 12 punti per ctg B")
    punteggio = models.FloatField(help_text="In base all'operatore selezionato"
                                            " viene assegnato all'intervallo temporale"
                                            " o a singole ore/mesi/anni dell'intervallo")
    operatore = models.CharField('Operatore da applicare al punteggio',
                                 help_text="Operatore che determina l'assegnazione",
                                 max_length=1, choices=_OPERATORI_PUNTEGGIO,
                                 default="a")
    note = models.CharField(max_length=255, blank=True,
                            help_text="Descrizione",
                            default="")
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)

    class Meta:
        verbose_name = _('Punteggio per durata temporale')
        verbose_name_plural = _('Punteggi per durata temporale')

    def get_intero_unita_temporale(self):
        """
        in base al valore d,m,y torna l'interno relativo

        # per discretizzazioni mesi/giorni implementare metodi
        specializzati con import calendar
        """
        return _UNITA_TEMPORALI_INT_MAP[self.unita_temporale]

    def get_operator_function(self):
        """
        in base al simbolo torna la funzione mappata in
        _MATH_OPERATOR_FUNC_MAP (import operator)
        """
        return _MATH_OPERATOR_FUNC_MAP[self.operatore]

    def check_corrispondenza_intervallo(self, cat_eco=None,intervallo=0):
        """
        Controlla se l'intervallo passato come argomento ricade nei
        limiti durata_minima e durata_massima del timedelta.
        Se l'argomento 'cat_eco' è settato, lo confronta con il self.pos_eco
        """
        if not intervallo: return False
        if cat_eco and cat_eco != self.pos_eco: return False
        return intervallo >= self.durata_minima and intervallo <= self.durata_massima

    def calcola_punteggio(self, durata):
        """
        durata è il secondo argomento del calcolo
        se invece è una assegnazione torna punteggio
        """
        if not self.get_operator_function():
            # se la funzione è nulla torna il punteggio
            return self.punteggio

        funzione_calcolo = self.get_operator_function()
        return funzione_calcolo(self.punteggio, durata)

    def __str__(self):
        if self.pos_eco:
            return '{}, {}: {}'.format(self.sub_descrizione_indicatore,
                                       self.pos_eco,
                                       self.punteggio)
        return '{}: {}'.format(self.sub_descrizione_indicatore,
                               self.punteggio)


class CategorieDisabilitate_DescrizioneIndicatore(models.Model):
    """
    Questa classe definisce quali categorie economiche
    vengono disabilitate per una DescrizioneIndicatore
    """

    descrizione_indicatore = models.ForeignKey(DescrizioneIndicatore,
                                               on_delete=models.CASCADE)
    posizione_economica = models.ManyToManyField(PosizioneEconomica, blank=True)
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)

    class Meta:
        verbose_name = _('Categoria Disabilitata Descrizione Indicatore')
        verbose_name_plural = _('Categorie Disabilitate Descrizione Indicatore')

    def __str__(self):
        return '{}'.format(self.descrizione_indicatore)


class RuoliDisabilitati_DescrizioneIndicatore(models.Model):
    """
    Questa classe definisce quali ruoli
    vengono disabilitati per una DescrizioneIndicatore
    """

    descrizione_indicatore = models.ForeignKey(DescrizioneIndicatore,
                                               on_delete=models.CASCADE)
    ruolo = models.CharField(choices = RUOLI, max_length=50,
                             blank=False, null=False, default='')
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)

    class Meta:
        unique_together = ('descrizione_indicatore', 'ruolo')
        verbose_name = _('Ruolo Disabilitato Descrizione Indicatore')
        verbose_name_plural = _('Ruoli Disabilitati Descrizione Indicatore')

    def __str__(self):
        return '{} - {}'.format(self.descrizione_indicatore, self.ruolo)


class CommissioneGiudicatrice(TimeStampedModel, CreatedModifiedModel):
    """
    """
    denominazione = models.CharField(max_length=255, default='')
    bando = models.ForeignKey(Bando, on_delete=models.CASCADE)
    data_inizio = models.DateTimeField()
    data_fine   = models.DateTimeField()
    note = models.TextField(blank=True, default='')
    accettazione_clausole_text = models.TextField('Testo Accettazione Clausole',
                                                  help_text=("es. Dichiaro di aver preso visione..."),
                                                  blank=True, null=True)
    is_active = models.BooleanField(help_text=_('Attiva'))

    def is_in_corso(self):
        if not self.is_active: return False
        if timezone.localtime() < self.data_inizio: return False
        if timezone.localtime() >= self.data_fine: return False
        return True

    def is_iniziata(self):
        return timezone.localtime() > self.data_inizio

    def is_terminata(self):
        return timezone.localtime() >= self.data_fine

    def get_clausole_attive(self):
        return ClausoleCommissioneGiudicatrice.objects.filter(commissione=self,
                                                              is_active=True)

    class Meta:
        verbose_name = _('Commissione giudicatrice')
        verbose_name_plural = _('Commissioni giudicatrici')

    def __str__(self):
        return '{} - {}'.format(self.denominazione, self.bando)


class CommissioneGiudicatriceUsers(TimeStampedModel, CreatedModifiedModel):
    """
    """
    commissione = models.ForeignKey(CommissioneGiudicatrice,
                                    on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ruolo = models.CharField(max_length=255, blank=True, null=True)
    clausole_accettate = models.BooleanField(default=False,
                                             help_text=_('Ha accettato le '
                                                         'clausole per la '
                                                         'partecipazione '
                                                         'alla commissione'))
    is_active = models.BooleanField(help_text=_('Attivo'))

    def ha_accettato_clausole(self):
        clausole = ClausoleCommissioneGiudicatrice.objects.filter(commissione=self.commissione,
                                                                  is_active=True)
        if not clausole: return True
        if self.clausole_accettate: return True
        return False

    class Meta:
        unique_together = ('commissione', 'user')
        verbose_name = _('Utente Commissione Giudicatrice')
        verbose_name_plural = _('Utenti Commissioni Giudicatrici')

    def __str__(self):
        return '{} - {}'.format(self.user, self.commissione)


class ClausoleCommissioneGiudicatrice(TimeStampedModel):
    """
    Crea le clausole del bando che ogni dipendete deve accettare prima
    di poter prender parte a una commissione giudicatrice
    """
    commissione = models.ForeignKey(CommissioneGiudicatrice,
                                    on_delete=models.CASCADE)
    titolo = models.CharField(max_length=255, blank=False, null=False,
                              help_text="Titolo clausola (es: Privacy...)")
    corpo_del_testo = models.TextField(help_text=("es. La partecipazione alla Commissione comporta..."),
                                       blank=False, null=False)
    ordinamento = models.PositiveIntegerField(help_text="posizione nell'ordinamento",
                                              blank=True, default=0)
    allegato = models.FileField(upload_to='allegati_clausola_partecipazione/commissioni/%m-%Y/',
                                null=True,blank=True)
    is_active = models.BooleanField('Visibile agli utenti', default=True)

    class Meta:
        ordering = ('ordinamento', )
        verbose_name = _('Clausola Commissione Giudicatrice')
        verbose_name_plural = _('Clausole Commissione Giudicatrice')

    def corpo_as_html(self):
        return text_as_html(self.corpo_del_testo)

    def __str__(self):
        return '({}) {}'.format(self.commissione, self.titolo)
