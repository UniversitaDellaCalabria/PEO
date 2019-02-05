import os
import pdfkit
import re

from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http.response import HttpResponse


def response_as_pdf(response, pdf_fname):
    """
    prende un oggetto http response e lo modifica per ottenere un pdf
    """
    html_page = response.content.decode('utf-8')

    # get static url from template tags (from django.contrib.staticfiles.templatetags.staticfiles import static)
    static_url = static('')
    production_static_url = settings.URL+static_url
    html_page_rewritten = re.sub(static_url,
                                 production_static_url, html_page)
    
    production_media_url = settings.URL+settings.MEDIA_URL
    html_page_rewritten = re.sub(settings.MEDIA_URL,
                                 production_media_url, html_page_rewritten)

    # f = open('/tmp/pdf_debug.html', 'w')
    # f.write(html_page_rewritten)
    # f.close()
    
    pdf_path = settings.TMP_DIR + os.path.sep + pdf_fname
    
    options = {
        'dpi':120,
        #'page-width': 2024,
        #'enable-smart-width': True,
        'page-size': 'A4',
        'background': None,
        'quiet': '',
        'no-outline': None,
        'margin-top': '0.2in',
        'margin-right': '0in',
        'margin-bottom': '0.2in',
        'margin-left': '0in',
    }
    # print(html_page_rewritten)
    pdf_stream = pdfkit.from_string(html_page_rewritten, 
                                    pdf_path,
                                    options=options)

    f = open(pdf_path, 'rb')
    response = HttpResponse(f.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=' + pdf_fname
    f.close()
    os.remove(pdf_path)
    return response
