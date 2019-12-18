import datetime, pytz

from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import render_to_response, get_object_or_404
from django import template

register = template.Library()

@register.simple_tag
def user_from_pk(user_id):
    if not user_id: return False
    user_model = get_user_model()
    user = user_model.objects.get(pk=user_id)
    if not user: return False
    return user
