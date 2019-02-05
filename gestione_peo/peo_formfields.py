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

from gestione_risorse_umane.models import Dipendente, TitoloStudio

from .settings import NUMERAZIONI_CONSENTITE


def _split_choices(choices_string):
    """
    Riceve una stringa e la splitta ogni ';'
    creando una tupla di scelte
    """
    str_split = choices_string.split(';')
    choices = tuple((x, x) for x in str_split)
    return choices


def _successivo_ad_oggi(data_da_valutare):
    """
    Ci dice se una data è successiva alla data di oggi
    """
    oggi = timezone.localtime().date()
    if data_da_valutare:
        return data_da_valutare > oggi


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


class PeoBaseCustomField(Field):
    """
    Classe Base che definisce i metodi per ogni CustomField
    """
    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def define_value(self,
                     domanda_bando=None,
                     descrizione_indicatore=None,
                     custom_value=None):
        """
        Integra la costruzione del field con informazioni aggiuntive
        provenienti dai parametri di configurazione definiti dall'utente
        """
        return

    def get_fields(self):
        """
        Se è un field semplice, torna se stesso.
        Se è un field composto, torna una lista di fields.
        """
        return [self]

    def raise_error(self, domanda_bando, fname, cleaned_data):
        """
        Torna la lista degli errori generati dalla validazoine del field
        """
        return []


class CustomCharField(CharField, PeoBaseCustomField):
    """
    CharField
    """
    titolo_classe = "Testo"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)


class CustomChoiceField(ChoiceField, PeoBaseCustomField):
    """
    ChoiceField
    """
    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def define_value(self, domanda_bando,
                     descrizione_indicatore, custom_value):
        """
        Se presenti, sostituisce alle opzioni di default
        quelle di 'custom_value'
        """
        if custom_value:
            elements = _split_choices(custom_value)
        self.choices = elements


class CustomFileField(FileField, PeoBaseCustomField):
    """
    FileField
    """
    titolo_classe = "Allegato PDF"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)


class PositiveIntegerField(DecimalField, PeoBaseCustomField):
    """
    Int DecimalField positivo
    """
    titolo_classe = "Numero intero positivo"
    default_validators = [MinValueValidator(0)]
    
    def __init__(self, **data_kwargs):
        # Non si accettano formati con cifre decimali
        data_kwargs['decimal_places'] = 0
        super().__init__(**data_kwargs)


class PositiveFloatField(DecimalField, PeoBaseCustomField):
    """
    Float DecimalField positivo
    """
    titolo_classe = "Numero con virgola positivo"
    default_validators = [MinValueValidator(0)]
    
    def __init__(self, **data_kwargs):
        # Max 3 cifre decimali
        data_kwargs['decimal_places'] = 3
        super().__init__(**data_kwargs)


class TextAreaField(CharField, PeoBaseCustomField):
    """
    TextArea
    """
    titolo_classe = "Testo lungo"
    widget = forms.Textarea()

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)


class CheckBoxField(BooleanField, PeoBaseCustomField):
    """
    BooleanField sottoforma di Checkbox
    """
    titolo_classe = "Checkbox"
    widget = forms.CheckboxInput()

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)


class PunteggioFloatField(PositiveFloatField):
    """
    Punteggio come FloatField positivo
    """
    titolo_classe = "Punteggio (numero con virgola)"
    name = "punteggio_dyn"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def define_value(self, domanda_bando,
                     descrizione_indicatore, custom_value):
        """
        Se DescrizioneIndicatore o Indicatore Ponderato prevedono
        un punteggio massimo, applica un validatore MaxValueValidator
        """
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
                

class TitoloStudioField(ModelChoiceField, PeoBaseCustomField):
    """
    SelectBox con i titoli di studio
    """
    titolo_classe = "Titoli di studio"
    name = "titolo_di_studio_superiore"

    def __init__(self, **data_kwargs):
        # Di default, inserisce tutti i titoli di studio definiti
        data_kwargs['queryset'] = TitoloStudio.objects.all()
        super().__init__(**data_kwargs)

    def define_value(self, domanda_bando,
                     descrizione_indicatore, custom_value):
        """
        Se per la categoria economica del Dipendente alcuni titoli
        di studio sono inibiti, li elimina dalla queryset
        """
        if domanda_bando:
            pos_eco = domanda_bando.dipendente.livello.posizione_economica
            punteggio_titoli = domanda_bando.bando. \
                               get_punteggio_titoli_pos_eco(pos_eco)
            if punteggio_titoli:
                self.queryset = punteggio_titoli
            else:
                self.queryset = TitoloStudio.objects.none()


class SubDescrizioneIndicatoreField(ModelChoiceField, PeoBaseCustomField):
    """
    SelectBox con le sotto-categorie SubDescrizioneIndicatore
    """
    titolo_classe = "Selezione sotto-categorie DescrizioneIndicatore"
    name = 'sub_descrizione_indicatore'

    def __init__(self, **data_kwargs):
        # Di default, inserisce tutti i SubDescrizioneIndicatore
        sub_descr_ind = apps.get_model('gestione_peo',
                                       'SubDescrizioneIndicatore')
        data_kwargs['queryset'] = sub_descr_ind.objects.all()
        super().__init__(**data_kwargs)

    def define_value(self, domanda_bando,
                     descrizione_indicatore, custom_value):
        """
        Se la DescrizioneIndicatore associata al Form prevede SubDescrInd
        li sostituisce ai valori di default
        """
        sub_descr_ind = None
        if descrizione_indicatore:
            sub_descr_ind = descrizione_indicatore. \
                            subdescrizioneindicatore_set.all()
        if sub_descr_ind:
            self.queryset = sub_descr_ind


class CustomSelectBoxField(CustomChoiceField):
    """
    SelectBox
    """
    titolo_classe = "Lista di opzioni (tendina)"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)
        elements = []

        # Imposta le 'choices' definite in backend come opzioni
        options = data_kwargs.get('choices')
        if options:
            elements = _split_choices(options)
        self.choices = elements


class CustomRadioBoxField(CustomChoiceField):
    """
    CheckBox multiplo
    """
    titolo_classe = "Lista di opzioni (checkbox)"
    widget = forms.RadioSelect()

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

        # Imposta le 'choices' definite in backend come opzioni
        elements = []
        options = data_kwargs.get('choices')
        if options:
            elements = _split_choices(options)
        self.choices = elements


class BaseDateField(DateField, PeoBaseCustomField):
    """
    DateField
    """
    titolo_classe = "Data"
    widget = forms.DateInput(attrs=_date_field_options)
    input_formats = settings.DATE_INPUT_FORMATS

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)


class BaseDateTimeField(DateTimeField):
    """
    DateTimeField
    """
    titolo_classe = "Data e Ora"
    widget = forms.DateInput(attrs=_date_field_options)
    input_formats = settings.DATE_INPUT_FORMATS

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)


class DateStartEndComplexField(PeoBaseCustomField):
    """
    Field composto da DataInizio (DateField) e DataFine (DateField)
    """
    titolo_classe = "Data inizio e Data fine"

    def __init__(self, **data_kwargs):
        # Data Inizio
        self.start = BaseDateField(**data_kwargs)
        self.start.required = True
        self.start.label = 'Data Inizio'

        # Riferimento a DateStartEndComplexField
        self.start.parent = self

        # Data Fine
        self.end = BaseDateField(**data_kwargs)
        self.end.required = True
        self.end.label = 'Data Fine'

        # Riferimento a DateStartEndComplexField
        self.end.parent = self

    def get_fields(self):
        fields = [self.start, self.end]
        return fields

    def raise_error(self, domanda_bando, name, cleaned_data):
        """
        Essendo un campo complesso che non ha riferimenti ai vincoli
        imposti dal bando, si eseguono solo i controlli standard sulle
        date di inizio e di fine
        """
        errors = []
        start_value = cleaned_data.get(self.start.name)
        end_value = cleaned_data.get(self.end.name)

        # Se il campo non viene correttamente inizializzato
        if not cleaned_data.get(name):
            return []

        # Si valuta 'Data Inizio'
        if name == self.start.name:
            # Se la data di inizio è successiva ad oggi
            if _successivo_ad_oggi(start_value):
                errors.append("La data di inizio non può "
                              "essere successiva ad oggi")
            # Se data_inizio > data_fine
            if end_value and start_value > end_value:
                errors.append("La data di inizio non può "
                              "essere successiva a quella di fine")

        # Si valuta 'Data Fine'
        if name == self.end.name:
            # Se la data di fine è successiva ad oggi
            if _successivo_ad_oggi(end_value):
                errors.append("La data di fine non può essere "
                              "successiva ad oggi")
        return errors


class DateInRangeComplexField(DateStartEndComplexField):
    """
    Field composto da DataInizio (DateField) e DataFine (DateField)
    che deve rigorisamente ricadere nel range imposto dal Bando
    (Data PresaServizio/UltimaProgressione - LimiteTitoli Bando)
    """
    titolo_classe = "Data inizio e Data fine IN RANGE of bando"

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

    def raise_error(self, domanda_bando, name, cleaned_data):
        """
        Questo campo complesso deve attenersi strettamente ai vincoli
        imposti dal bando, per cui, oltre a ereditard i controlli standard
        del parent, si eseguono ulteriori verifiche
        """
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progressione = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        errors = []
        # Recupero la lista di errori proveniente dai controlli del super
        errors = errors + (super().raise_error(domanda_bando,
                                               name,
                                               cleaned_data))

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


class DateInRangeInCorsoComplexField(DateInRangeComplexField):
    """
    Field composto da DataInizio (DateField), DataFine (DateField)
    e In Corso (BooleanField).
    Rispetta i vincoli del parent DateInRangeComplexField
    ma offre la possibilità di non specificare la data di fine (in corso)
    """
    titolo_classe = "Data inizio e Data fine IN RANGE of bando + 'In corso'"

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

    def raise_error(self, domanda_bando, name, cleaned_data):
        """
        Questo campo complesso dete attenersi strettamente ai vincoli
        imposti dal bando, per cui, oltre a ereditard i controlli standard
        del parent, si eseguono ulteriori verifiche
        """
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
            errors = errors + (super().raise_error(domanda_bando,
                                                   name,
                                                   cleaned_data))

        return errors


class DateOutOfRangeComplexField(DateStartEndComplexField):
    """
    Field composto da DataInizio (DateField) e DataFine (DateField)
    che deve rigorisamente ricadere fuori dal range imposto dal Bando
    (Data PresaServizio/UltimaProgressione - LimiteTitoli Bando)
    """
    titolo_classe = "Data inizio e Data fine OUT OF RANGE of bando"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

        self.start.name = 'data_inizio_dyn_out'
        self.end.name = 'data_fine_dyn_out'

    def raise_error(self, domanda_bando, name, cleaned_data):
        """
        Questo campo complesso deve attenersi strettamente ai vincoli
        imposti dal bando, per cui, oltre a ereditard i controlli standard
        del parent, si eseguono ulteriori verifiche
        """
        limite_validita_titoli = _limite_validita_titoli(domanda_bando)
        ultima_progressione = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[0]
        data_presa_servizio = \
            _ultima_progressione_data_presa_servizio(domanda_bando)[1]

        errors = []
        errors = errors + (super().raise_error(domanda_bando,
                                               name,
                                               cleaned_data))

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


class ProtocolloField(PeoBaseCustomField):
    """
    Tipo,Numero e Data protocollo (o altro tipo di numerazione)
    """
    titolo_classe = "Protocollo (tipo/numero/data)"

    def __init__(self, **data_kwargs):
        # Tipo protocollo. SelectBox
        self.tipo = CustomChoiceField(**data_kwargs)
        self.tipo.label = "Tipo"
        self.tipo.name = "tipo_numerazione_dyn"
        self.tipo.help_text = "Scegli se protocollo/decreto/delibera, " \
                              "al/alla quale la numerazione è riferita"
        self.tipo.choices = [(i.lower().replace(' ', '_'), i) \
                             for i in NUMERAZIONI_CONSENTITE]
        self.tipo.parent = self

        # Numero protocollo. CharField
        self.numero = CustomCharField(**data_kwargs)
        self.numero.required = True
        self.numero.label = "Numero"
        self.numero.name = "numero_protocollo_dyn"
        self.numero.help_text = "Indica il numero del " \
                                "protocollo/decreto/delibera"
        self.numero.parent = self

        # Data protocollo. DateField
        self.data = BaseDateField(**data_kwargs)
        self.data.name = "data_protocollo_dyn"
        self.data.label = "Data di riferimento alla numerazione"
        self.data.help_text = "Indica la data del protocollo/decreto/delibera"
        self.data.parent = self

    def get_fields(self):
        return [self.tipo, self.numero, self.data]

    def get_data_name(self):
        return self.data.name

    def raise_error(self, domanda_bando, name, cleaned_data):
        """
        Questo campo complesso subisce controlli inerenti i parametri
        imposti dal bando e allo stesso tempo si relaziona, se presente,
        a DataInizio e DataFine in range
        """
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


class CustomHiddenField(CharField, PeoBaseCustomField):
    """
    CharField Hidden
    """
    titolo_classe = "Campo nascosto"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def define_value(self, domanda_bando,
                     descrizione_indicatore, custom_value):
        self.widget = forms.HiddenInput(attrs={'value': custom_value})


class DurataComeInteroField(PositiveIntegerField):
    """
    Durata come Intero positivo
    """
    titolo_classe = "Durata come numero intero (anni,mesi,ore)"
    name = 'durata_come_intero'

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)


class DataLowerThanBandoField(BaseDateField):
    """
    DateField singolo all'interno dei limiti imposti dal bando
    """
    titolo_classe = "Data singola IN RANGE of bando"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def raise_error(self, domanda_bando, name, cleaned_data):
        """
        Questo campo deve rispettare i vincoli temporali del bando
        """
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


class AnnoInRangeOfCarrieraField(PositiveIntegerField):
    """
    Intero positivo per rappresentare un anno all'interno dei limiti
    temporali imposti dal bando
    """
    titolo_classe = "Anno singolo IN RANGE of bando"

    def __init__(self, **data_kwargs):
        super().__init__(**data_kwargs)

    def raise_error(self, domanda_bando, name, cleaned_data):
        """
        L'anno rappresentato, oltre alle validazioni su PositiveInteger,
        deve rispettare i limiti imposti dal bando e dalla carriera
        """
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
