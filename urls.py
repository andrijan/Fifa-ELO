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
)

if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        #(r"", include("staticfiles.urls")),
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_URL}),
    ) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
