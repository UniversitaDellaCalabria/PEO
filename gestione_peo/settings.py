from django.utils.translation import ugettext_lazy as _


NUMERAZIONI_CONSENTITE = [
                            'Protocollo',
                            'Decreto Rettorale (D.R.)',
                            'Decreto del Direttore Generale (D.D.G.)',
                            'Decreto del Direttore Dipartimento o Dirigente Struttura',
                            'Decreto del Direttore del Centro Residenziale (D.CR.)',
                            'Decreto del Prorettore (Centro Residenziale)',
                            'Delibera di Dipartimento/Facoltà',
                            'Delibera del Senato',
                            'Delibera del C.D.A.',
                         ]

# Campo testo "Etichetta" di default, creato automaticamente in ogni form
# di inserimento. Serve per l'individuazione rapida del modulo
# inserito da parte dell'utente ('id' e 'label' del field)
ETICHETTA_INSERIMENTI_ID = 'etichetta_inserimento'
ETICHETTA_INSERIMENTI_LABEL = 'Etichetta dell\'inserimento'
ETICHETTA_INSERIMENTI_HELP_TEXT = ('Il nome che desideri dare a questo modello compilato,'
                                   ' per individuarlo velocemente nella tua domanda')

COMPLETE_EMAIL_SENDER = 'peo-noreply@unical.it'
COMPLETE_EMAIL_SUBJECT = "{}, domanda trasmessa"
COMPLETE_EMAIL_BODY = """Caro {dipendente},

La tua domanda {bando} è stata correttamente trasmessa.
Per visionare il riepilogo di questa puoi collegarti al seguente url:

{url}{domanda_url}

Ti ricordiamo che attraverso la piattaforma sarà possibile
riaprire la domanda e ritrasmetterla fino alla data
di scadenza del bando.
"""

MOTIVAZIONE_DISABILITAZIONE_DUPLICAZIONE = "Disabilitazione per duplicazione in ({}) {}"
LOG_DUPLICAZIONE_MESSAGE = "Inserimento {origine} disabilitato e duplicato nella destinazione {destinazione}"

MODALITA_BONUS_ANZIANITA = ((0, _('Nessuna')),
                            (1, _('Moltiplicazione')),
                            (2, _('Punteggio aggiuntivo')))

RANGE_APPLICAZIONE_BONUS = ((0, _('Tutto')),
                            (1, _('Solo periodo attuale permanenza')),
                            (2, _('Solo periodo oltre validità minima')))
