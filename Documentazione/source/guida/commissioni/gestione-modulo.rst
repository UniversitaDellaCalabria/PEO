.. Procedura Elettronica Online (PEO) documentation master file, created by
   sphinx-quickstart on Tue Sep 11 08:57:06 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Gestione singolo inserimento
============================

La gestione di un singolo modulo di inserimento prevede azioni diverse in base all'utente che lo ha creato.

* **Se il modulo è stato creato dal dipendente proprietario della domanda** il commissario può esclusivamente disabilitare (con opportuna motivazione) o riabilitare l'inserimento, al fine di preservare l'integrità dei dati inseriti dall'utente;
* **Se il modulo è stato creato da un componente della commissione**, invece, può essere modificato/eliminato/disabilitato/riabilitato da lui e da tutti gli altri membri. L'attività di integrazione di una domanda, infatti, deve essere reversibile in tutto il periodo di attività della commissione.

.. thumbnail:: images/gestione_modulo_disabilita.png

**Duplicazione**

La duplicazione di un inserimento ad opera di un commissario automatizza il più possibile le operazioni manuali di disabilitazione e conseguente creazione di un modulo e prevede le seguenti fasi:

.. image:: images/gestione_modulo_duplica_button.png

* Scelta *Descrizione Indicatore Ponderato* di destinazione;
* Pre-compilazione del form di destinazione con i campi comuni a quello della *sorgente*;
* Compilazione dei campi mancanti (ed eventuale integrazione di quelli pre-compilati);
* Salvataggio.

Questa serie di operazioni, se completate con successo, portano alla disabilitazione con una motivazione standard (presente nei *settings* del progetto) dell'inserimento *sorgente* e alla creazione di un nuovo inserimento nella nuova destinazione.