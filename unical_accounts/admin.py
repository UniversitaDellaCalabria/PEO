from django.contrib import admin
from django.utils.translation import ugettext, ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin

from .models import User
from .admin_inlines import *

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    readonly_fields = ('date_joined', 'last_login',)
    list_display = ('username', 'matricola', 'email', 'is_active', 'is_staff', 'is_superuser', )
    list_editable = ('is_active', 'is_staff', 'is_superuser',)
    fieldsets = (
        (None, {'fields': (('username', 'is_active', 'is_staff', 'is_superuser', ),
                           ('password'),
                           )}),
        (_('Angrafica'), {'fields': (( 'first_name', 'last_name'),
                                         ( 'matricola', 'email'),
                                         ('codice_fiscale',),
                                         ('gender', 'location', 'birth_date',),
                                        )}),
        
        (_('Permissions'), {'fields': ('groups', 'user_permissions'),
                            'classes':('collapse',)
                            ,}),
                           
        
        (_('Date accessi sistema UNICAL PEO'), {'fields': (('date_joined', 
                                                            'last_login', ),
                                                          )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
