from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _

"""
    <div class="ui small breadcrumb" style="padding: 0;">
      <a href="/" class="section">Pagina principale</a>
      <div class="divider"> / </div>
      <a class="active  section">La tua Domanda {{ bando.nome }}</a>
    </div>
"""

class BreadCrumbs(object):
    def __init__(self, 
                 css_cls="ui small breadcrumb",
                 url_list = []):
        """
            url_list = [(reverse('app_name:url', args=[]), ('Label to display')), ...]
        """
        self.css_cls = css_cls
        self.root = settings.HOME_PAGE
        self.url_list = url_list
    
    def as_html(self):
        html = '<div class="{}" style="padding: 0;">'.format(self.css_cls)
        node = '<a href="{}" class="{} section">{}</a>'
        root = node.format(self.root, '', _("Pagina principale"))
        divider = '<div class="divider"> / </div>'
        base = html+root+divider
        if self.url_list:
            for url in self.url_list[:-1]:
                base += node.format(url[0], '', url[1])
                base += divider
            # last is the active node
            active_url = self.url_list[-1]
            base += node.format(active_url[0], 'active', active_url[1])
        base += '</div>'
        return base
    
    
    def add_url(self, url_values=()):
        if url_values not in self.url_list:
            self.url_list.append(url_values)
        else:
            # se è già inserito rimuovi i successivi (pulisci il path)
            pos = self.url_list.index(url_values)
            self.url_list = self.url_list[:pos+1]
    
    def reset(self):
        self.url_list = []
