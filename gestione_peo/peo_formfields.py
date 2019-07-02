import datetime
import os

from django import forms
from django.apps import apps
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ModelChoiceField
from django.forms.fields import *
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.translation import gettext as _

from django_form_builder.dynamic_fields import *
from django_form_builder.utils import *
from gestione_risorse_umane.models import Dipendente, TitoloStudio

from .settings import NUMERAZIONI_CONSENTITE


def _limite_validita_titoli(domanda_bando):
    """
    Torna 'limite_validita_titoli' del bando a cui la domanda
    si riferisce
    """
    bando = domanda_bando.bando
    limite_validita_titoli = bando.data_validita_titoli_fine
    return limite_validita_titoli


def _ultima_progressione_data_presa_servizio(domanda_bando):
    """
    Torna una tuplua con 'data_ultima_progressione' e
    'data_presa_servizio' del dipendente che ha creato la domanda
    """
    dipendente = domanda_bando.dipendente
    bando = domanda_bando.bando
    ultima_progressione = dipendente.get_data_progressione().date()
    data_presa_servizio = dipendente.get_data_presa_servizio_csa().date()

    # OVERRIDE delle date progressione e presa_servizio SE queste sono
    # maggiori di bando.ultima_progressione SE E SOLO SE il dipendente
    # risulta essere stato abilitato a partecipare da ARU.
    # Questo evita che incoerenze delle interpretazioni di carriera lato CSA
    # confliggano con la decisione di ARU di abilitare un dipendente
    # alla partecipazione. Questo consente di inserire titoli relativi
    # ad un delta tra bando.ultima_progressione e
    # bando.data_validita_titoli_fine.
    # Se il dipendente dovesse in aggiunta inserire ulteriori pregressi
    # li dovrebbe innanzitutto intervenire ARU sui dati presenti in CSA
    if dipendente.idoneita_peo_attivata():
        if ultima_progressione > bando.ultima_progressione:
            ultima_progressione = bando.ultima_progressione
        if data_presa_servizio > bando.ultima_progressione:
            data_presa_servizio = bando.ultima_progressione
    # Questo risolve i conflitti che potrebbero incorrere
    # tra una decisione di ARU e il comportamento del sistema
    return (ultima_progressione, data_presa_servizio)


# 'type':'date', <- confligge con datepicker che serve solo per ie11
_date_field_options = {'class': 'datepicker'}


class PEO_BaseDateField(BaseDateField):
    """
    DateField
    """
    widget = forms.DateInput(attrs=_date_field_options)


class PEO_BaseDateTimeField(BaseDateTimeField):
    """
    DateTimeField
    """
    widget = forms.DateInput(attrs=_date_field_options)


class PEO_PunteggioFloatField(PositiveFloatField):
    """
    Punteggio come FloatField positivo
    """
    field_type = _("_PEO_  Punteggio (numero con virgola)")
    name = "punteggio_dyn"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def define_value(self, custom_value, **kwargs):
        """
        Se DescrizioneIndicatore o Indicatore Ponderato prevedono
        un punteggio massimo, applica un validatore MaxValueValidator
        """
        domanda_bando = kwargs.get('domanda_bando')
        descrizione_indicatore = kwargs.get('descrizione_indicatore')
        if domanda_bando:
            posizione_economica = domanda_bando.dipendente. \
                livello.posizione_economica
            p_max = descrizione_indicatore. \
                get_pmax_pos_eco(posizione_economica)
            if not p_max:
                p_max = descrizione_indicatore.indicatore_ponderato. \
                    get_pmax_pos_eco(posizione_economica)
            #if p_max and not any(isinstance(x, MaxValueValidator)
            #                     for x in self.default_validators):
            if p_max:
                #self.default_validators.append(MaxValueValidator(p_max))
                self.validators.append(MaxValueValidator(p_max))
                


class PEO_TitoloStudioField(ModelChoiceField, BaseCustomField):
    """
    SelectBox con i titoli di studio
    """
    field_type = _("_PEO_  Titoli di studio")
    name = "titolo_di_studio_superiore"

    def __init__(self, **data_kwargs):
        # Di default, inserisce tutti i titoli di studio definiti
        data_kwargs['queryset'] = TitoloStudio.objects.all()
        super().__init__(**data_kwargs)

    def define_value(self, custom_value, **kwargs):
        """
        Se per la categoria economica del Dipendente alcuni titoli
        di studio sono inibiti, li elimina dalla queryset
        """
        domanda_bando = kwargs.get('domanda_bando')
        descrizione_indicatore = kwargs.get('descrizione_indicatore')
        if domanda_bando:
            pos_eco = domanda_bando.dipendente.livello.posizione_economica
            punteggio_titoli = domanda_bando.bando. \
                               get_punteggio_titoli_pos_eco(pos_eco)
            if punteggio_titoli:
                self.queryset = punteggio_titoli
            else:
                self.queryset = TitoloStudio.objects.none()


class PEO_SubDescrizioneIndicatoreField(ModelChoiceField, BaseCustomField):
    """
    SelectBox con le sotto-categorie SubDescrizioneIndicatore
    """
    field_type = _("_PEO_  Selezione sotto-categorie DescrizioneIndicatore")
    name = 'sub_descrizione_indicatore'

    def __init__(self, **data_kwargs):
        # Di default, inserisce tutti i SubDescrizioneIndicatore
        sub_descr_ind = apps.get_model('gestione_peo',
                                       'SubDescrizioneIndicatore')
        data_kwargs['queryset'] = sub_descr_ind.objects.all()
        super().__init__(**data_kwargs)

    def define_value(self, custom_value,**kwargs):
        """
        Se la DescrizioneIndicatore associata al Form prevede SubDescrInd
        li sostituisce ai valori di default
        """
        domanda_bando = kwargs.get('domanda_bando')
        descrizione_indicatore = kwargs.get('descrizione_indicatore')
        sub_descr_ind = None
        if descrizione_indicatore:
            sub_descr_ind = descrizione_indicatore. \
                            subdescrizioneindicatore_set.all()
        if sub_descr_ind:
            self.queryset = sub_descr_ind


class PEO_DateStartEndComplexField(DateStartEndComplexField):
    """
    Field composto da DataInizio (DateField) e DataFine (DateField)
    """
    field_type = _("_PEO_ Data inizio e Data fine")
    is_complex = True

    def __init__(self, *args, **data_kwargs):
        # Data Inizio
        self.start = PEO_BaseDateField(*args, **data_kwargs)
        self.start.required = True
        self.start.label = _('Data Inizio')
        self.start.name = "data_inizio_dyn"

        # Riferimento a DateStartEndComplexField
        self.start.parent = self

        # Data Fine
        self.end = PEO_BaseDateField(*args, **data_kwargs)
        self.end.required = True
        self.end.label = _('Data Fine')
        self.end.name = "data_fine_dyn"

        # Riferimento a DateStartEndComplexField
        self.end.parent = self


class PEO_DateInRangeComplexField(PEO_DateStartEndComplexField):
    """
    Field composto da DataInizio (DateField) e DataFine (DateField)
    che deve rigorisamente ricadere nel range imposto dal Bando
    (Data PresaServizio/UltimaProgressione - LimiteTitoli Bando)
    """
    field_type = _("_PEO_  Data inizio e Data fine IN RANGE of bando")
    is_complex = True

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

        # Definizione 'name' dei field Inizio e Fine
        # Tutti gli altri parametri sono inizializzati tramite il super
        self.start.name = 'data_inizio_dyn_inner'
        self.end.name = 'data_fine_dyn_inner'

    def get_start_name(self):
        return self.start.name

    def get_end_name(self):
        return self.end.name

    def raise_error(self, name, cleaned_data, **kwargs):
        """
        Questo campo complesso deve attenersi strettamente ai vincoli
        imposti dal bando, per cui, oltre a ereditard i controlli standard
        del parent, si eseguono ulteriori verifiche
        """
        domanda_bando = kwargs.get('domanda_bando')
        if not domanda_bando: return []
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progressione = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        errors = []
        # Recupero la lista di errori proveniente dai controlli del super
        errors = errors + (super().raise_error(name,
                                               cleaned_data,
                                               **kwargs))

        value = cleaned_data.get(name)

        # Se il campo non viene correttamente inizializzato
        if not value:
            return []

        # Si valuta 'Data Inizio'
        if name == self.start.name:
            # Se la data di inizio è successiva al limite imposto dal bando
            if value > limite_validita_titoli:
                errors.append("La data di inizio non può"
                              " essere successiva al"
                              " {}".format(limite_validita_titoli))
            # Se la data di inizio è precedente alla presa di servizio
            if value < data_presa_servizio:
                errors.append("La data di inizio non può essere precedente"
                              " alla presa di servizio:"
                              " {}".format(data_presa_servizio))

            # Check con Field Protocollo se presente
            protocollo = ProtocolloField()
            data_protocollo_name = protocollo.get_data_name()
            data_protocollo = cleaned_data.get(data_protocollo_name)

            # Se nel form è presente il protocollo
            # e la data di inizio è precedente a quella di protocollo
            if data_protocollo and value < data_protocollo:
                errors.append("La data di inizio non può essere"
                              " precedente alla data del protocollo")
        # Si valuta 'Data Fine'
        elif name == self.end.name:
            # Se la data di fine è precedente all'ultima progressione
            if value < ultima_progressione:
                errors.append("La data di fine è precedente all'ultima"
                              " progressione effettuata:"
                              " {}".format(ultima_progressione))
        return errors


class PEO_DateInRangeInCorsoComplexField(PEO_DateInRangeComplexField):
    """
    Field composto da DataInizio (DateField), DataFine (DateField)
    e In Corso (BooleanField).
    Rispetta i vincoli del parent DateInRangeComplexField
    ma offre la possibilità di non specificare la data di fine (in corso)
    """
    field_type = _("_PEO_  Data inizio e Data fine IN RANGE of bando + 'In corso'")
    is_complex = True

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

        self.end.required = False

        # BooleanField aggiuntivo
        self.in_corso = CheckBoxField(**data_kwargs)
        self.in_corso.required = False
        self.in_corso.widget = forms.CheckboxInput()
        self.in_corso.label = 'In corso'
        self.in_corso.name = 'in_corso_dyn'
        self.in_corso.parent = self

    def get_in_corso_name(self):
        return self.in_corso.name

    def get_fields(self):
        ereditati = super().get_fields()
        ereditati.extend([self.in_corso])
        return ereditati

    def raise_error(self, name, cleaned_data, **kwargs):
        """
        Questo campo complesso dete attenersi strettamente ai vincoli
        imposti dal bando, per cui, oltre a ereditard i controlli standard
        del parent, si eseguono ulteriori verifiche
        """
        domanda_bando = kwargs.get('domanda_bando')
        if not domanda_bando: return []
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progressione = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        errors = []

        value = cleaned_data.get(name)
        end_value = cleaned_data.get(self.end.name)

        # Si valuta 'In corso'
        if name == self.in_corso.name:
            # Se è definito anche Data Fine
            if value and end_value:
                errors.append("Compilare solo uno dei campi"
                              " 'Data Fine' e 'Incarico in corso'")
            # Se non è definito nè In Corso nè Data Fine
            if not value and not end_value:
                errors.append("Compilare almeno uno dei campi"
                              " 'Data Fine' e 'Incarico in corso'")
        # Se valuto gli altri fields recupero gli altri errori
        else:
            errors = errors + (super().raise_error(name,
                                                   cleaned_data,
                                                   **kwargs))

        return errors


class PEO_DateOutOfRangeComplexField(DateStartEndComplexField):
    """
    Field composto da DataInizio (DateField) e DataFine (DateField)
    che deve rigorisamente ricadere fuori dal range imposto dal Bando
    (Data PresaServizio/UltimaProgressione - LimiteTitoli Bando)
    """
    field_type = _("_PEO_  Data inizio e Data fine OUT OF RANGE of bando")
    is_complex = True

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

        self.start.name = 'data_inizio_dyn_out'
        self.end.name = 'data_fine_dyn_out'

    def raise_error(self, name, cleaned_data, **kwargs):
        """
        Questo campo complesso deve attenersi strettamente ai vincoli
        imposti dal bando, per cui, oltre a ereditard i controlli standard
        del parent, si eseguono ulteriori verifiche
        """
        domanda_bando = kwargs.get('domanda_bando')
        if not domanda_bando: return []
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progressione = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        errors = []
        errors = errors + (super().raise_error(name,
                                               cleaned_data,
                                               **kwargs))

        value = cleaned_data.get(name)

        if not value:
            return []

        # Si valuta 'Data Inizio'
        if name == self.start.name:
            # Se la data di inizio è successiva alla presa di servizio
            if value > data_presa_servizio:
                errors.append("La data di inizio non può essere successiva "
                              "alla presa di servizio: "
                              "{}".format(data_presa_servizio))
        # Si valuta 'Data Fine'
        elif name == self.end.name:
            # Se la data di fine è successiva alla presa di servizio
            if value > data_presa_servizio:
                errors.append("La data di fine non può essere successiva "
                              "alla presa di servizio: "
                              "{}".format(data_presa_servizio))
        return errors


class PEO_DataLowerThanBandoField(PEO_BaseDateField):
    """
    DateField singolo all'interno dei limiti imposti dal bando
    """
    field_type = _("_PEO_  Data singola IN RANGE of bando")

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def raise_error(self, name, cleaned_data, **kwargs):
        """
        Questo campo deve rispettare i vincoli temporali del bando
        """
        domanda_bando = kwargs.get('domanda_bando')
        if not domanda_bando: return []
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progressione = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        if ultima_progressione == data_presa_servizio:
            ultima_progressione = False

        errors = []
        value = cleaned_data.get(name)

        if not value:
            return ['Valore non presente']

        # Se la data è successiva al termine imposto dal bando
        if value > limite_validita_titoli:
            errors.append("La data non può essere successiva"
                          " al limite imposto dal bando:"
                          " {}".format(limite_validita_titoli))
        # Se la data è precedente all'ultima progressione
        if ultima_progressione and (value < ultima_progressione):
            errors.append("La data non può essere precedente all'ultima "
                          "progressione effettuata: {} "
                          .format(ultima_progressione))
        # Se la data è precedente alla presa di servizio
        if value < data_presa_servizio:
            errors.append("La data non può essere precedente alla presa "
                          "di servizio: {}".format(data_presa_servizio))
        return errors


class PEO_AnnoInRangeOfCarrieraField(PositiveIntegerField):
    """
    Intero positivo per rappresentare un anno all'interno dei limiti
    temporali imposti dal bando
    """
    field_type = _("_PEO_  Anno singolo IN RANGE of bando")

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def raise_error(self, name, cleaned_data ,**kwargs):
        """
        L'anno rappresentato, oltre alle validazioni su PositiveInteger,
        deve rispettare i limiti imposti dal bando e dalla carriera
        """
        domanda_bando = kwargs.get('domanda_bando')
        if not domanda_bando: return []
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progressione = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        if ultima_progressione == data_presa_servizio:
            ultima_progressione = False

        errors = []
        value = cleaned_data.get(name)

        if not value:
            return ["Specificare un valore valido"]

        # Se è successivo all'anno di 'limite_validita_titoli' del bando
        if value > limite_validita_titoli.year:
            errors.append("Questo anno non può essere superiore a "
                          "quello della data limite imposta dal bando: "
                          "{}".format(bando.data_validita_titoli_fine.year))
        # Se è successivo all'anno dell'ultima progressione
        if ultima_progressione and (value < ultima_progressione.year):
            errors.append("Questo anno non può essere precedente a "
                          "quello dell'ultima progressione effettuata: "
                          "{}".format(ultima_progressione.year))
        # Se è successivo all'anno della presa di servizio
        if value < data_presa_servizio.year:
            errors.append("Questo anno non può essere precedente a "
                          "quello della presa di servizio: "
                          "{}".format(data_presa_servizio.year))
        return errors


class PEO_ProtocolloField(ProtocolloField):
    field_type = _("_PEO_  Protocollo (tipo/numero/data)")
    is_complex = True

    def raise_error(self, name, cleaned_data, **kwargs):
        """
        Questo campo complesso subisce controlli inerenti i parametri
        imposti dal bando e allo stesso tempo si relaziona, se presente,
        a DataInizio e DataFine in range
        """
        domanda_bando = kwargs.get('domanda_bando')
        if not domanda_bando: return []
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progr = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        if ultima_progr == data_presa_servizio:
            ultima_progr = False

        value = cleaned_data.get(name)

        if not value:
            return ["Valore mancante"]

        # Si valuta 'Data protocollo'
        if name == self.data.name:
            errors = []
            # Se la data è successiva al limite imposto dal bando
            if value > limite_validita_titoli:
                errors.append("La data di protocollo non può"
                              " essere successiva al"
                              " {}".format(limite_validita_titoli))
            # Se la data è successiva ad oggi
            if _successivo_ad_oggi(value):
                errors.append("La data di protocollo non può essere"
                              " successiva ad oggi")
            # Se la data è precedente alla presa di servizio
            if value < data_presa_servizio:
                errors.append("La data di protocollo non può essere"
                              " precedente alla presa di servizio:"
                              " {}".format(data_presa_servizio))

            # Serve interfacciarsi con DateInRangeInCorsoComplexField
            d = DateInRangeInCorsoComplexField()

            in_corso_name = d.get_in_corso_name()
            in_corso = cleaned_data.get(in_corso_name)

            data_fine_name = d.get_end_name()
            data_fine = cleaned_data.get(data_fine_name)

            data_inizio_name = d.get_start_name()
            data_inizio = cleaned_data.get(data_inizio_name)

            # Se NON è stato checkato il campo "fino_ad_oggi"
            # e la data di fine è precedente all'ultima progressione,
            # l'incarico non è continuativo
            if not in_corso:
                if ultima_progr and data_fine and data_fine < ultima_progr:
                    if value < ultima_progr:
                        errors.append("La data del protocollo "
                                      "è precedente all'ultima "
                                      "progressione effettuata: "
                                      "{}".format(ultima_progr))

            # Se non esistono i campi Data allora non
            # siamo in grado di capire se l'incarico è di tipo continuativo,
            # per cui la data del protocollo deve essere sempre precedente
            # all'ultima progressione effettuata
            if not data_inizio:
                if ultima_progr and data_protocollo < ultima_progr:
                    errors.append("La data del protocollo è precedente "
                                  "all'ultima progressione effettuata: "
                                  "{}".format(ultima_progr))
            return errors
