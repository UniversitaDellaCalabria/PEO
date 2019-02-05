import logging

from django.conf import settings
from django.shortcuts import render

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.views.static import serve



