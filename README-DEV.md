Rebuild con migrations rebased
------------------------------

````
mysql -u root -e "DROP DATABASE $DB;"

mysql -u root -e "\
CREATE DATABASE ${DB} CHARACTER SET utf8 COLLATE utf8_general_ci;\
GRANT ALL PRIVILEGES ON ${DB}.* TO ${USER}@'${HOST}';"

find . -type f | grep ".pyc" | xargs rm

./manage.py makemigrations
./manage.py migrate
bash loaddatas.sh
````

#### CINECA CSA

Il sistema PEO non dipende da CINECA CSA ma usa questo per allineare i dati.
Questo significa che puoi allineare/creare/gestire i tuoi dati come meglio preferisci.
Ti conviene mantenere la struttura del modello dati così come esposto in csa/models.py
per evitare di dover apporre modifiche.

Se le colonne del tuo DB dovessero chiamarsi diversamente rispetto a CSA, puoi modificare il
mapping in csa/models.py, modifica solo i valori e non le chiavi per garantire il funzionamento del codice:

````
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
                        #'relaz_accomp': 'relaz_accomp',
                        'ruolo': 'ruolo'}
````

Migrazione dati denominazioni PeoDynamicForm fields
---------------------------------------------------
**Solo per sviluppatori**

Nuove denominazioni dei field con 'name' statico contenuti in PEO 2018
````
data_inizio# : data_inizio_dyn_inner
data_fine# : data_fine_dyn_inner
fino_ad_oggi# : in_corso_dyn
data_inizio_# : data_inizio_dyn_out
data_fine_# : data_fine_dyn_out
tipo_numerazione : tipo_numerazione_dyn
numero_protocollo : numero_protocollo_dyn
data_protocollo : data_protocollo_dyn
punteggio : punteggio_dyn

````

Field con 'name' statico (in PEO 2018) che diventano dinamici.
(Controllo sui form di ogni DescrizioneIndicatore per rilevare il nuovo slug).
````
anno_in_range_of_carriera : anno_pubblicazione (presente in PEO 2018 solo in Ea)
data_lower_than_bando : slug dinamico da definizione field (campo mai utilizzato in PEO 2018)

````

Denominazioni rimaste invariate
````
durata_come_intero : durata_come_intero
sub_descrizione_indicatore : sub_descrizione_indicatore
domanda_bando_id : domanda_bando_id
titolo_di_studio_superiore : titolo_di_studio_superiore

````

Procedura di migrazione delle denominazioni
````
from domande_peo.models import *
from gestione_peo.models import *
bando = Bando.objects.filter(slug="peo-2018").first()
domande = DomandaBando.objects.filter(bando=bando).all()
for domanda in domande:
    print(domanda.dipendente)
    for mdb in domanda.modulodomandabando_set.all():
        mdb.migrate_fieldname('data_inizio#', 'data_inizio_dyn_inner')
        mdb.migrate_fieldname('data_fine#', 'data_fine_dyn_inner')
        mdb.migrate_fieldname('fino_ad_oggi#', 'in_corso_dyn')
        mdb.migrate_fieldname('data_inizio_#', 'data_inizio_dyn_out')
        mdb.migrate_fieldname('data_fine_#', 'data_fine_dyn_out')
        mdb.migrate_fieldname('tipo_numerazione', 'tipo_numerazione_dyn')
        mdb.migrate_fieldname('numero_protocollo', 'numero_protocollo_dyn')
        mdb.migrate_fieldname('data_protocollo', 'data_protocollo_dyn')
        mdb.migrate_fieldname('punteggio', 'punteggio_dyn')
        mdb.migrate_fieldname('anno_in_range_of_carriera', 'anno_pubblicazione')
````

Update tabella 'gestione_peo.moduloinserimentocampi'.
````
mod_ins_campi_migration_dict = {
    'CharField' : 'CustomCharField',
    'TextField' : 'TextAreaField',
    'IntegerField' : 'PositiveIntegerField',
    'FloatField' : 'PositiveFloatField',
    'PunteggioFloatField' : 'PunteggioFloatField',
    '_TitoloStudioField' : 'TitoloStudioField',
    '_SubDescrizioneIndicatoreField' : 'SubDescrizioneIndicatoreField',
    'FileField' : 'CustomFileField',
    'CheckBoxField' : 'CheckBoxField',
    'CustomSelectBoxField' : 'CustomSelectBoxField',
    'CustomRadioBoxField' : 'CustomRadioBoxField',
    'ProtocolloField' : 'ProtocolloField',
    'DateField' : 'BaseDateField',
    'StartEndDateField' : 'DateInRangeInCorsoComplexField',
    'StartEndDateField_2' : 'DateInRangeComplexField',
    'OutStartEndDateField' : 'DateOutOfRangeComplexField',
    'DataLowerThanBandoField' : 'DataLowerThanBandoField',
    'AnnoInRangeOfCarrieraField' : 'AnnoInRangeOfCarrieraField',
    'DurataComeInteroField' : 'DurataComeInteroField',
}

for i in mod_ins_campi_migration_dict:
    c = ModuloInserimentoCampi.objects.filter(tipo = i)
    #print(i, c)
    c.update(tipo = mod_ins_campi_migration_dict[i])

````

Procedura di test per rilevare incongruenze in seguito alla migrazione.
````
from domande_peo.models import *
from gestione_peo.models import *
bando = Bando.objects.filter(slug = "peo-2018").first()
domande = DomandaBando.objects.filter(bando = bando).all()
for domanda in domande:
    print(domanda.dipendente)
    for mdb in domanda.modulodomandabando_set.filter(disabilita = False):
        try:
            form = mdb.compiled_form()
            if not mdb.allegati_validi() or not form.is_valid():
                print("Domanda PEO", domanda)
                print("Modulo non valido")
                print("Denominazione", mdb)
                print("ID", mdb.id)
                print()
        except Exception as e:
            print("Eccezione {}".format(e), mdb.id, domanda.dipendente)
            continue
````

Installazione Sphinx (solo development)
---------------------------------------
Sphinx serve per la produzione della documentazione della piattaforma.

````
sphinx-quickstart Documentazione

Separate source and build directories (y/n) [n]: y
Name prefix for templates and static dir [_]: peo_
Project name: Procedura Elettronica Online (PEO)
Author name(s): Giuseppe De Marco, Francesco Filicetti
Project release []: 1.0
Project language [en]: it
Source file suffix [.rst]: .rst
Name of your master document (without suffix) [index]:
Do you want to use the epub builder (y/n) [n]: y
autodoc: automatically insert docstrings from modules (y/n) [n]: y
doctest: automatically test code snippets in doctest blocks (y/n) [n]: n
intersphinx: link between Sphinx documentation of different projects (y/n) [n]: n
todo: write "todo" entries that can be shown or hidden on build (y/n) [n]: y
coverage: checks for documentation coverage (y/n) [n]: n
imgmath: include math, rendered as PNG or SVG images (y/n) [n]:
mathjax: include math, rendered in the browser by MathJax (y/n) [n]:
ifconfig: conditional inclusion of content based on config values (y/n) [n]: y
viewcode: include links to the source code of documented Python objects (y/n) [n]: y
githubpages: create .nojekyll file to publish the document on GitHub pages (y/n) [n]: n

Create Makefile? (y/n) [y]: y
Create Windows command file? (y/n) [y]: y
````
