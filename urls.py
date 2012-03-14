import os

from django.conf import settings
from django.conf.urls.defaults import *
from django.conf.urls.static import static

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^admin/', include(admin.site.urls)),
    
    (r'^', include('core.urls')),
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/assets/static/img/favicon.ico'}),
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        #(r"", include("staticfiles.urls")),
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.ROOT_PATH, 'assets')}, name='media'),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.STATIC_ROOT, 'static')}, name='static'),
    ) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
