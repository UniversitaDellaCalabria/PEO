import json

from django.utils import timezone

# DEPRECATO: non considera DATE_INPUT_FORMAT bensì regexp dichiarate localmente alla classe! (abominio)
#from django.utils.dateparse import parse_date

from django_form_builder.utils import get_as_dict
from gestione_peo.models import Punteggio_TitoloStudio
from gestione_peo.peo_formfields import _inizio_validita_titoli
from unical_template.utils import (differenza_date_in_mesi_aru,
                                   parse_date_string as parse_date)


class PunteggioDomandaBando(object):
    """
    Raccoglie tutti i metodi relativi al calcolo del punteggio di una
    DomandaBando
    """

    _warning_message = 'SOGLIA SUPERATA : {} - Dichiarato: {} / Max: {} / Decurtato: {}'

    def calcola_punteggio_anzianita_automatico(self):
        """
        Torna il punteggio assegnato all'anzianità di servizio
        considerando anche gli eventuali "bonus" previsti nel bando
        """
        punteggio = 0
        punteggio_categoria = 0

        # mesi_anzianita = self.dipendente.get_anzianita_mesi()

        # if not mesi_anzianita:
            # return punteggio

        data_limite = self.bando.data_validita_titoli_fine

        # Presa servizio
        presa_servizio = self.get_presa_servizio_dipendente()
        mesi_servizio = differenza_date_in_mesi_aru(presa_servizio,
                                                    data_limite)
        if mesi_servizio == 0:
            return punteggio

        # Permanenza nella stessa categoria
        ultima_progressione = self.get_ultima_progressione_dipendente()
        mesi_permanenza = differenza_date_in_mesi_aru(ultima_progressione,
                                                      data_limite)
        unita_temporale = "m"

        # Se nel bando è impostata l'assegnazione di punti per l'anzianità
        if self.bando.punteggio_anzianita_servizio_set.first():
            for fascia in self.bando.punteggio_anzianita_servizio_set.all():
                unita_temporale = fascia.unita_temporale
                if fascia.posizione_economica == self.get_livello_dipendente().posizione_economica:
                    punteggio_categoria = fascia.punteggio
                    break
                elif not fascia.posizione_economica:
                    punteggio_categoria = fascia.punteggio

            if unita_temporale=="m":
                punteggio += punteggio_categoria*mesi_servizio
            elif unita_temporale=="y":
                punteggio += punteggio_categoria*(mesi_servizio/12)

            # Se non è stata effettuata alcuna progressione e
            # l'anzianità è maggiore o uguale alla soglia di bonus
            if ultima_progressione == presa_servizio and \
            mesi_servizio >= 12*self.bando.agevolazione_soglia_anni:
                punteggio = punteggio*self.bando.agevolazione_fatmol
            # Se la data di progressione è diversa dalla presa servizio
            elif ultima_progressione != presa_servizio:
                #Se è soddisfatta la condizione del bando, si applica il bonus di moltiplicazione
                if mesi_permanenza >= 12*self.bando.agevolazione_soglia_anni:
                    # Poichè i mesi di permanenza sono stati già considerati prima
                    # la moltiplicazione la faccio per 'fatmol-1' e aggiungo il 'plus'
                    bonus = punteggio_categoria*mesi_permanenza*(self.bando.agevolazione_fatmol-1)
                    punteggio += bonus
        return punteggio

    def get_punteggio_anzianita(self):
        if self.punteggio_anzianita_manuale:
            punteggio =  self.punteggio_anzianita_manuale
        else:
            punteggio = self.calcola_punteggio_anzianita_automatico()
        return float("{:.2f}".format(punteggio))

    def calcolo_punteggio_sub_descr(self,
                                    descr_ind,
                                    categoria_economica,
                                    sub_descr_valutati,
                                    mdb,
                                    calcolo):
        """
        Aggiorna la lista dei sub_descr_ind già valutati e
        valuta se la somma dei punteggi ha raggiunto la soglia
        massima ammissibile
        """
        # Lista ritornata come risultato
        # [0] = punteggio ottenuto senza tener conto di alcuna soglia
        # [1] = punteggio reale assegnato (max)
        # [2] = eventuale messaggio di sforamento
        punteggi = [0, 0, '']

        # Recupero l'id del sub_descr
        sub_id = mdb.contain_sub_descr_ind()
        # Recupero l'oggetto
        sub_descr_ind = descr_ind.subdescrizioneindicatore_set.filter(pk=sub_id).first()
        # Controllo che il sub_descr abbia una soglia max
        # per categoria economica
        p_max_sub_descr = sub_descr_ind.get_pmax_pos_eco(categoria_economica)
        if p_max_sub_descr:
            # Se avevo già valutato inserimento dello stesso
            # sub_descr_ind sommo il punteggio
            if sub_descr_valutati.get(sub_id):
                sub_descr_valutati[sub_id][0] += calcolo
            # Se è la prima occorrenza del descr_ind che
            # trovo nella domanda, memorizzo un riferimento
            else:
                sub_descr_valutati[sub_id] = punteggi
                sub_descr_valutati[sub_id][0] = calcolo

            punteggio_accumulato = sub_descr_valutati[sub_id][0]
            # Controllo che non venga superata la soglia massima
            if punteggio_accumulato > p_max_sub_descr:
                sub_descr_valutati[sub_id][1] = p_max_sub_descr
                sub_descr_valutati[sub_id][2] = self._warning_message.format('({}) {} - {}'.format(sub_descr_ind.descrizione_indicatore.id_code,
                                                                                                   sub_descr_ind.descrizione_indicatore,
                                                                                                   sub_descr_ind),
                                                                             float("{:.2f}".format(punteggio_accumulato)),
                                                                             p_max_sub_descr,
                                                                             float("{:.2f}".format(punteggio_accumulato-p_max_sub_descr))
                                                                            )
            # Se non viene superata la soglia, attribuisco il punteggio accumulato
            else:
                sub_descr_valutati[sub_id][1] = punteggio_accumulato
            return sub_descr_valutati


    def calcolo_punteggio_max_descr_ind(self,
                                        descr_ind,
                                        categoria_economica,
                                        ignora_disabilitati=False,
                                        save=False):
        """
        Per ogni DescrizioneIndicatore, calcola i punteggi dei relativi
        ModuliCompilati, restituendo il punteggio MAX in base alle soglie
        (di ogni Descr_Ind) definite in fase di configurazione
        """
        p_max_descr_ind = descr_ind.get_pmax_pos_eco(categoria_economica)

        # Punteggio assegnato alla DescrizioneIndicatore
        p_descrizione_indicatore = 0
        # Punteggio assegnato alla DescrizioneIndicatore senza soglie
        p_descrizione_indicatore_senza_soglie = 0
        # Eventuale lista di messaggi di sforamento soglie
        messaggi = []
        # Lista ritornata come risultato
        # [0] = punteggio ottenuto senza tener conto di alcuna soglia
        # [1] = punteggio reale assegnato (max)
        # [2] = eventuale messaggio di sforamento
        results = [p_descrizione_indicatore_senza_soglie,
                   p_descrizione_indicatore,
                   messaggi]

        # Parametri valutazione titolo di studio più alto (o cumulativo)
        p_titolo_studio = p_titolo_studio_cumulato = 0
        priorita_titoli = self.bando.priorita_titoli_studio
        titoli_valutati = []

        # Dizionario che, per ogni SubDescrizioneIndicatore valutato,
        # contiene i punteggi ad esso assegnati e gli eventuali
        # messaggi di sforamento (vedi calcolo_punteggio_sub_descr())
        sub_descr_valutati = {}

        # Per ogni ModuloCompilato della Domanda,
        # controllo se il punteggio ottenuto
        # supera il MassimoPunteggio per CategoriaEconomica
        # impostato per quella DescrizioneIndicatore
        if self.modulodomandabando_set.filter(descrizione_indicatore=descr_ind):
            for mdb in self.modulodomandabando_set.filter(descrizione_indicatore=descr_ind):

                # Se il Modulo è stato disabilitato
                # e si deve tener conto dei titoli disabilitati
                if mdb.disabilita and not ignora_disabilitati:
                    continue

                # Lancio il metodo calcolo_punteggio che mi setta
                # il punteggio del modulo sul backend
                calcolo = mdb.calcolo_punteggio(save=save)

                # Se si tratta di valutare un titolo di studio
                titolo = mdb.punteggio_titolo_studio()
                if titolo:

                    # Se è il primo elemento a essere valutato
                    # inizializzo i parametri
                    if not titoli_valutati:
                        titoli_valutati.append(titolo[0])
                        p_titolo_studio = titolo[1]
                        p_titolo_studio_cumulato = titolo[1]
                    # Se il titolo è superiore a quelli valutati
                    # e non è presente nella lista di quelli già esaminati
                    elif titolo[1] > p_titolo_studio and titolo[0] not in titoli_valutati:
                        titoli_valutati.append(titolo[0])
                        p_titolo_studio = titolo[1]
                        if priorita_titoli:
                            p_titolo_studio_cumulato = titolo[1]
                        else:
                            p_titolo_studio_cumulato += titolo[1]
                    # Se il titolo di studio è inferiore a quelli valutati
                    # e non c'è la priorità, il suo punteggio si va a sommare al totale
                    elif titolo[1] <= p_titolo_studio and titolo[0] not in titoli_valutati:
                        titoli_valutati.append(titolo[0])
                        if not priorita_titoli:
                            p_titolo_studio_cumulato += titolo[1]
                    # Se il titolo è cumulabile o ha punteggio uguale
                    # o maggiore a 'p_titolo_studio' (il max punteggio rilevato)
                    # si va a sommare al totale
                    elif titolo[0] in titoli_valutati and titolo[2]:
                        if not priorita_titoli or titolo[1] >= p_titolo_studio:
                            p_titolo_studio_cumulato += titolo[1]

                    p_descrizione_indicatore = p_titolo_studio_cumulato

                # Se si valuta un SubDecrizioneIndicatore
                elif mdb.contain_sub_descr_ind():

                    lista_tmp = self.calcolo_punteggio_sub_descr(descr_ind,
                                                                 categoria_economica,
                                                                 sub_descr_valutati,
                                                                 mdb,
                                                                 calcolo)
                    # Se il sub_descr_ind ha soglie massime
                    # di punteggio da rispettare
                    if lista_tmp:
                        sub_descr_valutati = lista_tmp

                    # Se non c'è soglia, sommo il punteggio calcolato
                    # al punteggio della DescrizioneIndicatore
                    else:
                        p_descrizione_indicatore += calcolo

                # Se non si stanno valutando titoli di studio nè sub_descr
                else:
                    p_descrizione_indicatore += calcolo

            # Imposto il punteggio calcolato senza soglie
            # uguale a quello fino ad ora cumulato
            # Non sono ancora state effettuate verifiche sulle soglie
            p_descrizione_indicatore_senza_soglie = p_descrizione_indicatore

            # Sommo al punteggio della DescrizioneIndicatore i "massimi"
            # ottenuti dai sub_descr valutati (se esistono)
            if len(sub_descr_valutati)>0:
                for p_max in sub_descr_valutati:
                    # Cumulo i punteggi calcolati senza soglie
                    p_descrizione_indicatore_senza_soglie += sub_descr_valutati[p_max][0]
                    # Cumulo i punteggi che tengono conto delle soglie
                    p_descrizione_indicatore += sub_descr_valutati[p_max][1]
                    # Popolo la lista dei messaggi
                    messaggio_sub_descr = sub_descr_valutati[p_max][2]
                    if messaggio_sub_descr:
                        messaggi.append(messaggio_sub_descr)

            # Aggiorno la lista da ritornare
            results = [p_descrizione_indicatore_senza_soglie,
                       p_descrizione_indicatore,
                       messaggi]

            # Infine, rispetto la soglia MAX della DescrizioneIndicatore
            if p_max_descr_ind > 0 and p_descrizione_indicatore > p_max_descr_ind:
                messaggi.append(self._warning_message.format('({}) {}'.format(descr_ind.id_code, descr_ind),
                                                             float("{:.2f}".format(p_descrizione_indicatore)),
                                                             p_max_descr_ind,
                                                             float("{:.2f}".format(p_descrizione_indicatore-p_max_descr_ind))
                                                            ))
                # Imposto come punteggio di cui tener conto il max
                results[1] = p_max_descr_ind
                # Imposto la lista dei messaggi
                results[2] = messaggi
        return results

    def calcolo_punteggio_max_indicatore(self,
                                         indicatore,
                                         categoria_economica,
                                         ignora_disabilitati=False,
                                         save=False):
        """
        Per ogni IndicatorePonderato, calcola i punteggi dei relativi
        ModuliCompilati, restituendo il punteggio MAX in base alle soglie
        (di ogni Indicatore) definite in fase di configurazione
        """
        # Soglia massima assegnabile
        p_max_indicatore = indicatore.get_pmax_pos_eco(categoria_economica)
        # Punteggio assegnato all'Indicatore Ponderato
        p_indicatore = 0
        # Punteggio assegnato all'Indicatore Ponderato senza soglie
        p_indicatore_senza_soglie = 0
        # Eventuale lista di messaggi di sforamento soglie
        messaggi = []
        # Lista ritornata come risultato
        # [0] = punteggio ottenuto senza tener conto di alcuna soglia
        # [1] = punteggio reale assegnato (max)
        # [2] = eventuale messaggio di sforamento
        results = [p_indicatore_senza_soglie,
                   p_indicatore,
                   messaggi]

        # Se si somma punteggio anzianità di servizio interna
        if indicatore.add_punteggio_anzianita:
            p_indicatore = self.get_punteggio_anzianita()
            p_indicatore_senza_soglie = self.get_punteggio_anzianita()

        # Per ogni DescrizioneIndicatore dell'Indicatore in questione
        # con calcolo_punteggio_automatico = True

        if indicatore.descrizioneindicatore_set.filter(calcolo_punteggio_automatico=True):
            for descr_ind in indicatore.descrizioneindicatore_set.filter(calcolo_punteggio_automatico=True):
                # Punteggio DescrInd incrementa punteggio Indicatore
                results_descr_ind = self.calcolo_punteggio_max_descr_ind(descr_ind=descr_ind,
                                                                     categoria_economica=categoria_economica,
                                                                     ignora_disabilitati=ignora_disabilitati,
                                                                     save=save)
                # Cumulo i punteggi che non tengono conto delle soglie
                p_indicatore_senza_soglie += results_descr_ind[0]
                # Cumulo i punteggi che tengono conto delle soglie
                p_indicatore += results_descr_ind[1]
                # Popolo la lista dei messaggi
                messaggi.extend(results_descr_ind[2])

            # Aggiorno la lista da ritornare
            results = [p_indicatore_senza_soglie,
                       p_indicatore,
                       messaggi]

            # Controllo sul Max punteggio CatEco IndicatorePonderato
            if p_max_indicatore > 0 and p_indicatore > p_max_indicatore:
                messaggi.append(self._warning_message.format('({}) {}'.format(indicatore.id_code, indicatore),
                                                             float("{:.2f}".format(p_indicatore)),
                                                             p_max_indicatore,
                                                             float("{:.2f}".format(p_indicatore-p_max_indicatore))
                                                            ))
                # Imposto come punteggio reale la soglia max
                results[1] = p_max_indicatore
                # Imposto i messaggi
                results[2] = messaggi
        return results

    def calcolo_punteggio_tot_moduli_compilati(self,
                                               ignora_disabilitati=False,
                                               save=False):
        """
        Torna il punteggio totale relativo ai ModuliCompilati
        riferiti a DescrizioneIndicatori con calcolo_punteggio_automatico=True
        """
        punteggio = 0
        punteggio_senza_soglie = 0
        messaggi = []

        if self.modulodomandabando_set.first() or self.bando.indicatore_con_anzianita():
            categoria_economica = self.get_livello_dipendente().posizione_economica

            # Per ogni IndicatorePonderato del Bando
            for indicatore in self.bando.indicatoreponderato_set.all():

                results_indicatore = self.calcolo_punteggio_max_indicatore(indicatore=indicatore,
                                                                     categoria_economica=categoria_economica,
                                                                     ignora_disabilitati=ignora_disabilitati,
                                                                     save=save)
                # Punteggio cumulato senza tener conto delle soglie
                punteggio_senza_soglie += results_indicatore[0]
                # Punteggio che tiene conto di tutte le soglie
                punteggio += results_indicatore[1]
                # Messaggi
                messaggi.extend(results_indicatore[2])

        punteggio = float("{:.2f}".format(punteggio))
        punteggio_senza_soglie = float("{:.2f}".format(punteggio_senza_soglie))
        results = [punteggio_senza_soglie,
                   punteggio,
                   messaggi]
        return results

    def calcolo_punteggio_domanda(self,
                                  save=False,
                                  ignora_disabilitati=False):

        if not self.dipendente:
            return [0, 0, []]

        results = self.calcolo_punteggio_tot_moduli_compilati(ignora_disabilitati=ignora_disabilitati,
                                                              save=save)

        if save:
            self.punteggio_calcolato = results[1]
            self.save()
        return results


class PunteggioModuloDomandaBando(object):
    """
    Raccoglie tutti i metodi relativi al calcolo del punteggio di un
    modulo di inserimento
    """
    def punteggio_descrizione_indicatore(self,
                                         cat_eco,
                                         sub_descr_ind=None):
        """
        Torna il punteggio della DescrizioneIndicatore
        se questa prevede un punteggio "fisso" per categoria economica
        """
        punteggio = 0
        descr_ind = self.descrizione_indicatore
        if not sub_descr_ind:
            fasce_punteggio = descr_ind.punteggio_descrizioneindicatore_set.all()
        else:
            fasce_punteggio = sub_descr_ind.punteggio_subdescrizioneindicatore_set.all()

        for fascia_punteggio in fasce_punteggio:
            if fascia_punteggio.pos_eco and fascia_punteggio.pos_eco==cat_eco:
                # Interrompo il for solo se sono sulla mia posizione economica
                return fascia_punteggio.punteggio
            # se invece il campo pos_eco non è settato, continuo a ciclare, potrei trovarla
            elif not fascia_punteggio.pos_eco:
                punteggio = fascia_punteggio.punteggio

        return punteggio


    def get_durata_int(self,
                       durata_inserita=0,
                       data_inizio=None,
                       data_fine=None,
                       fino_ad_oggi=None,
                       data_inizio_out=None,
                       data_fine_out=None):
        """
        Restituisce un INTERO corrispondente all'intervallo temporale
        derivante dai campi inseriti dall'utente.
        Il campo numerico 'data_inserita' ha la priorità sui campi Date
        'data_inizio' e 'data_fine'/'fino_ad_oggi'
        """
        # Format Date e controllo "fino ad oggi" e ultima_progressione
        inizio = termine = None

        dipendente = self.domanda_bando.dipendente
        ultima_progressione = self.domanda_bando.get_ultima_progressione_dipendente()

        # soglia data inizio validità titoli
        soglia = _inizio_validita_titoli(self.domanda_bando.bando,
                                         ultima_progressione)

        if durata_inserita:
            return durata_inserita

        # Se nel form è stato inserito il campo "intervallo date IN RANGE Bando"
        elif data_inizio:
            inizio = parse_date(data_inizio)
            if soglia and (inizio < soglia):
                inizio = soglia
            if data_fine:
                termine = parse_date(data_fine)
                # Se la data di fine va oltre il termine di validità
                # dei titoli imposto dal bando, allora lo stesso termine
                # viene considerato come data_fine
                if termine > self.domanda_bando.bando.data_validita_titoli_fine:
                    termine = self.domanda_bando.bando.data_validita_titoli_fine
            if fino_ad_oggi:
                termine = self.domanda_bando.bando.data_validita_titoli_fine
            # Calcolo numero di mesi nell'intervallo delle date
            return differenza_date_in_mesi_aru(inizio, now=termine)

        # Se nel form è stato inserito il campo "intervallo date OUT OF RANGE Bando"
        elif data_inizio_out:
            inizio = parse_date(data_inizio_out)
            termine = parse_date(data_fine_out)
            # Calcolo numero di mesi nell'intervallo delle date
            return differenza_date_in_mesi_aru(inizio, now=termine)
        return 0

    def punteggio_descr_timedelta(self,
                                  cat_eco,
                                  durata=0,
                                  sub_descr_ind=None):
        """
        Se la DescrizioneIndicatore lo prevede
        torna il punteggio della fascia TimeDelta corrispondente
        alla categoria economica del dipendente e all'intervallo temporale
        in cui l'inserimento ricade
        """
        punteggio = 0

        if not durata: return punteggio

        # Accettati i Float ma valutati solo come Interi
        durata = int(durata)

        descr_ind = self.descrizione_indicatore

        if not sub_descr_ind:
            regole = descr_ind.punteggio_descrizioneindicatore_timedelta_set.all()
        else:
            regole = sub_descr_ind.punteggio_subdescrizioneindicatore_timedelta_set.all()

        for regola in regole:
            # regola è un oggetto timedelta
            unita_temporale = regola.unita_temporale

            # Se la regola è associata a una particolare categoria economica
            if regola.pos_eco:
                # Se è la mia categoria economica,
                # e l'intervallo è verificato
                if regola.check_corrispondenza_intervallo(cat_eco, durata):
                    return regola.calcola_punteggio(durata)

            # Se alla regola non è associata una categoria economica
            # (non faccio mai "return" perchè, andando avanti, potrei
            # trovare la regola per la mia categoria economica)
            elif regola.check_corrispondenza_intervallo(None,durata):
                punteggio = regola.calcola_punteggio(durata)

        return punteggio

    def punteggio_titolo_studio(self):
        """
        Calcolo del punteggio attribuito al titolo di studio
        """
        if self.descrizione_indicatore.calcolo_punteggio_automatico:
            json_dict = json.loads(self.modulo_compilato)
            dati_inseriti = get_as_dict(json_dict)
            if "titolo_di_studio_superiore" in dati_inseriti:
                titolo_studio = Punteggio_TitoloStudio.objects.get(pk=dati_inseriti.get("titolo_di_studio_superiore"))
                result = [titolo_studio.titolo,
                          titolo_studio.punteggio,
                          titolo_studio.cumulabile]
                return result

    def contain_sub_descr_ind(self):
        """
        True se il modulo compilato contiene un SubDescrizioneIndicatore
        """
        json_dict = json.loads(self.modulo_compilato)
        dati_inseriti = get_as_dict(json_dict)
        if "sub_descrizione_indicatore" in dati_inseriti:
            return dati_inseriti.get("sub_descrizione_indicatore")

    def calcolo_punteggio(self, save=False):
        """
        Calcolo automatico del punteggio assegnato al Modulo Compilato
        che è collegato a una particolare DescrizioneIndicatore
        Questo metodo non tiene conto del limite max di punteggio assegnabile
        che sarà rispettato in fase di assegnazione del punteggio alla Domanda
        """
        punteggio = 0
        descr_ind = self.descrizione_indicatore

        # Se la DescrizioneIndicatore ha il calcolo punteggio automatico
        if descr_ind.calcolo_punteggio_automatico:
            json_dict = json.loads(self.modulo_compilato)
            dati_inseriti = get_as_dict(json_dict)
            dipendente = self.domanda_bando.dipendente
            cat_eco = self.domanda_bando.get_livello_dipendente().posizione_economica
            # Se il form prevede un campo Punteggio
            if "punteggio_dyn" in dati_inseriti:
                punteggio =  float(dati_inseriti.get("punteggio_dyn"))

            # Se il form prevede un campo "Titolo di Studio" con punteggio
            elif "titolo_di_studio_superiore" in dati_inseriti:
                punteggio_titolo = self.punteggio_titolo_studio()
                punteggio = float(punteggio_titolo[1])

            # Se il form prevede la selezione di un SubDescrizioneIndicatore
            elif "sub_descrizione_indicatore" in dati_inseriti:
                subdescrind_id = dati_inseriti.get("sub_descrizione_indicatore")
                subdescrind = descr_ind.subdescrizioneindicatore_set.filter(pk=subdescrind_id).first()

                if subdescrind.punteggio_subdescrizioneindicatore_set.first():
                    punteggio = self.punteggio_descrizione_indicatore(cat_eco,
                                                                      subdescrind)
                elif subdescrind.punteggio_subdescrizioneindicatore_timedelta_set.first():
                    durata_inserita = int(dati_inseriti.get("durata_come_intero", 0))
                    durata = self.get_durata_int(durata_inserita,
                                                 dati_inseriti.get("data_inizio_dyn_inner"),
                                                 dati_inseriti.get("data_fine_dyn_inner"),
                                                 dati_inseriti.get("in_corso_dyn"),
                                                 dati_inseriti.get("data_inizio_dyn_out"),
                                                 dati_inseriti.get("data_fine_dyn_out"))
                    punteggio = self.punteggio_descr_timedelta(cat_eco,
                                                               durata,
                                                               subdescrind)
            # Se la DescrizioneIndicatore prevede un punteggio "fisso" per categoria
            elif descr_ind.punteggio_descrizioneindicatore_set.first():
                punteggio = self.punteggio_descrizione_indicatore(cat_eco)
            # Se la DescrizioneIndicatore prevede un punteggio per durata temporale
            # WARNING: stiamo usando costanti, da ricodare con metodi che tornano i valori/tipi
            elif descr_ind.punteggio_descrizioneindicatore_timedelta_set.first():
                try:
                    durata_inserita = int(dati_inseriti.get("durata_come_intero", 0))
                except ValueError as excp:
                    durata_inserita = 0
                    # aggiungere logger.error in ogni dove ...
                durata = self.get_durata_int(durata_inserita,
                                             dati_inseriti.get("data_inizio_dyn_inner"),
                                             dati_inseriti.get("data_fine_dyn_inner"),
                                             dati_inseriti.get("in_corso_dyn"),
                                             dati_inseriti.get("data_inizio_dyn_out"),
                                             dati_inseriti.get("data_fine_dyn_out"))
                punteggio = self.punteggio_descr_timedelta(cat_eco, durata)

        if save:
            self.punteggio_calcolato = punteggio
            self.save()
        return punteggio
