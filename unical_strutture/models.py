from django.db import models
#from ckeditor.fields import RichTextField

class FunzioneLocazioneStruttura(models.Model):
    """
    descrive la funzione assolta da una struttura
    """
    nome = models.CharField(max_length=128, blank=True, unique=True)
    descrizione = models.TextField(max_length=768, null=True,blank=True)
    data_inserimento = models.DateTimeField(auto_now=True) 

    class Meta:
        ordering = ['nome']
        verbose_name = "Funzione di una Struttura"
        verbose_name_plural = "Funzioni di una Struttura"

    def __str__(self):
        return '%s' % self.nome

class TipoStruttura(models.Model):
    """
    aula, dipartimento, segreteria, centro, servizio(mensa, alloggio...)
    """
    nome = models.CharField(max_length=128, blank=True, unique=True)
    descrizione = models.TextField(max_length=768, null=True,blank=True)
    data_inserimento = models.DateTimeField(auto_now=True) 

    class Meta:
        ordering = ['nome']
        verbose_name = "Tipologia di Struttura"
        verbose_name_plural = "Tipologie di Struttura"

    def __str__(self):
        return '%s' % self.nome


class Struttura(models.Model):
    """
    dipartimento, aula, laboratorio
    """
    nome = models.CharField(max_length=255, blank=True, unique=True)
    tipo = models.ForeignKey(TipoStruttura, null=True, blank=True,
                             on_delete=models.SET_NULL)
    #descrizione = RichTextField(max_length=12000, null=True,blank=True)
    descrizione = models.TextField(max_length=1024, null=True,blank=True)
    data_inserimento = models.DateTimeField(auto_now=True)
    url = models.CharField(max_length=768, null=True, blank=True)
    sede = models.CharField(max_length=255, null=True,blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']
        verbose_name = "Struttura"
        verbose_name_plural = "Strutture"        

    def __str__(self):
        if not self.tipo:
            return self.nome
        return '%s, %s' % (self.nome, self.tipo)

class TipoDotazione(models.Model):
    nome = models.CharField(max_length=128, blank=True, unique=True)
    descrizione = models.TextField(max_length=1024, null=True,blank=True)
    class Meta:
        ordering = ['nome']
        verbose_name = "Tipo di dotazione tecnica o strutturale"        
        verbose_name_plural = "Tipi di dotazione tecnica o strutturale"        

    def __str__(self):
        return '%s' % self.nome

class Locazione(models.Model):
    """
    luogo fisico
    """
    nome = models.CharField(max_length=128, unique=True)
    indirizzo = models.CharField(max_length=768, null=True,blank=True)
    coordinate = models.CharField(max_length=64, null=True,blank=True)
    srs = models.CharField(max_length=13, null=True,blank=True, 
                           help_text="riferimento spaziale coordinate")
    descrizione_breve = models.CharField(max_length=255, null=True,blank=True)
    descrizione = models.TextField(max_length=1024, null=True,blank=True)
    data_inserimento = models.DateTimeField(auto_now=True) 

    class Meta:
        ordering = ['nome']
        verbose_name = "Locazione"
        verbose_name_plural = "Locazioni"

    def __str__(self):
        return '%s' % self.nome

class LocazioneStruttura(models.Model):
    """
    una struttura può essere dislocata in più locazioni
    """
    locazione = models.ForeignKey(Locazione,
                                  on_delete=models.CASCADE)
    struttura = models.ForeignKey(Struttura,
                                  on_delete=models.CASCADE)
    funzione = models.ManyToManyField(FunzioneLocazioneStruttura, blank=True)
    dotazione = models.ManyToManyField(TipoDotazione)
    telefono =  models.CharField(max_length=135, null=True,blank=True)
    descrizione_breve = models.CharField(max_length=255, null=True,blank=True)
    descrizione = models.TextField(max_length=1024, null=True,blank=True)
    nota = models.TextField(max_length=1024, null=True,blank=True,
                            help_text=("Descrivere lo stato della struttura nella locazione."
                                       " Esempio: Momentaneamente chiusa, allagata, problemi"
                                       " lavori in corso, previsioni"))
    is_active = models.BooleanField(default=True)
    class Meta:
        ordering = ['struttura']
        verbose_name = "Locazione di una Struttura"
        verbose_name_plural = "Locazioni di una Struttura"

    def __str__(self):
        return '%s - %s' % (self.struttura, self.locazione)
