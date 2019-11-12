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
]
