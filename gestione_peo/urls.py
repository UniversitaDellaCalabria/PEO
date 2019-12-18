"""django_peo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import *

app_name="gestione_peo"

urlpatterns = [
    path('bandi/<str:bando_id>/', dettaglio_bando_peo, name='dettaglio_bando_peo'),
    path('bandi', bandi_peo, name='bandi_peo'),
    path('bandi/import_file', import_file, name='import_file'),
    path('bandi/<str:bando_id>/avvisi/<int:avviso_id>/download/', download_avviso, name='download_avviso'),

    # Commissione bando
    path('commissioni', commissioni, name='commissioni'),
    path('commissioni/<int:commissione_id>/', commissione_dettaglio, name='dettaglio_commissione'),
    path('commissioni/<int:commissione_id>/gestisci', commissione_manage, name='manage_commissione'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>', commissione_domanda_manage, name='commissione_domanda_manage'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/extended', commissione_domanda_manage_extended, name='commissione_domanda_manage_extended'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/modulo/<int:modulo_id>/download_allegato/<str:allegato>/',commissione_download_allegato, name='commissione_download_allegato'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/modulo/<int:modulo_id>/elimina_allegato/<str:allegato>/',commissione_elimina_allegato, name='commissione_elimina_allegato'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/abilita', commissione_abilita_domanda, name='commissione_abilita_domanda'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/disabilita', commissione_disabilita_domanda, name='commissione_disabilita_domanda'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/aggiungi', commissione_domanda_scegli_titolo, name='commissione_domanda_scegli_titolo'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/aggiungi/<int:descrizione_indicatore_id>', commissione_domanda_aggiungi_titolo, name='commissione_domanda_aggiungi_titolo'),

    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/modulo/<int:modulo_id>/duplica', commissione_domanda_duplica_titolo, name='commissione_domanda_duplica_titolo'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/modulo/<int:modulo_id>/duplica/<int:descrizione_indicatore_id>', commissione_domanda_duplica_titolo_confirm, name='commissione_domanda_duplica_titolo_confirm'),

    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/modulo/<int:modulo_id>/modifica', commissione_modulo_domanda_modifica, name='commissione_modulo_domanda_modifica'),
    path('commissioni/<int:commissione_id>/gestisci/domande/<int:domanda_id>/modulo/<int:modulo_id>/cancella', commissione_cancella_titolo, name='commissione_cancella_titolo'),
]
