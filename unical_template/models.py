from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.fields import AutoCreatedField, AutoLastModifiedField

class CreatedModifiedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    related_name="modified-%(app_label)s_%(class)s_related+",
                                    related_query_name="modified-%(app_label)s_%(class)ss+",
                                    on_delete=models.CASCADE, editable=False
                                    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                                   related_name="created-%(app_label)s_%(class)s_related+",
                                   related_query_name="created-%(app_label)s_%(class)ss+",
                                   on_delete=models.CASCADE, editable=False
                                   )

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created = AutoCreatedField(_('created'), editable=False)
    modified = AutoLastModifiedField(_('modified'), editable=False)

    class Meta:
        abstract = True
