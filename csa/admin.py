from django.contrib import admin
from django.contrib import messages
from django.utils.safestring import mark_safe
from unical_template.admin import ReadOnlyAdmin

from . models import *

class CustomReadOnlyModelAdmin(admin.ModelAdmin):
    def has_add_permission(cls, request):
        ''' remove add and save and add another button '''
        return False

    # Allow viewing objects but not actually changing them.
    def has_change_permission(self, request, obj=None):
        if request.method in ['GET', 'HEAD'] and \
           super().has_change_permission(request, obj):
            return True
        # else:
            # messages.add_message(request, messages.ERROR, 'Non possiamo modificare i dati in CSA!')
        
    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):        
        # messages.add_message(request, messages.ERROR, 'Non possiamo modificare i dati in CSA!')
        return False

    def response_post_save_change(self, request, obj):
        # get messages
        # storage = messages.get_messages(request)
        #print(storage.__dict__)
        # remove messages "X changed succesfully"
        # del storage._loaded_messages[0]
        pass

    def delete_selected(self, request, obj):
        pass

    class Media:
        css = {'all': ('css/no-admin-submit.css',),}
        js = ('js/readonly_input_fields.js',)
    
@admin.register(V_ANAGRAFICA)
class V_ANAGRAFICA_Admin(CustomReadOnlyModelAdmin):
    list_display = ('matricola', 'nome', 'cognome', 'email',)
    search_fields = ('email', 'matricola', 'cognome', 'nome')
    readonly_fields = ('get_incarichi_csa', 'get_carriera_csa')

    fields = ('matricola',
                ('nome', 'cognome'),
                ('email', 'cod_fis'),
                'get_incarichi_csa',
                'get_carriera_csa',
             )
    
    def get_incarichi_csa(self, obj):
        d = obj.get_incarichi_view()
        if not d: return ''
        html_rows = []
        for i in d[0].keys():
            html_rows.append('<th>{}<th>'.format(i))
        for i in d:
            html_rows.append('<tr>')
            for row in i:
                html_rows.append('<td>{}<td>'.format(i[row]))
            html_rows.append('</tr>')
        return mark_safe('<table>{}</table>'.format(''.join(html_rows)))
    get_incarichi_csa.short_description = 'Incarichi presenti in CSA'

    def get_carriera_csa(self, obj):
        d = obj.get_carriera_docente_view() or obj.get_carriera_view()       
        if not d: return ''        
        html_rows = []
        for i in d[0].keys():
            html_rows.append('<th>{}<th>'.format(i))
        for i in d:
            html_rows.append('<tr>')
            for row in i:
                html_rows.append('<td>{}<td>'.format(i[row]))
            html_rows.append('</tr>')
        return mark_safe('<table>{}</table>'.format(''.join(html_rows)))
    get_carriera_csa.short_description = 'Carriera in CSA'

@admin.register(V_RUOLO)
class V_RUOLO_Admin(CustomReadOnlyModelAdmin):
    list_filter = ('tipo_ruolo', 'ruolo')
    list_display = ('ruolo', 'tipo_ruolo', 'comparto', 'descr',)

# @admin.register(V_CARRIERA)
# class V_CARRIERA_Admin(admin.ModelAdmin):
    # list_filter = ('data_inizio', 'data_fine')
    # list_display = ('matricola', 'num_doc', 'data_inizio', 'data_fine', 'relaz_accomp')
