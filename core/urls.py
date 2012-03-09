from django.conf.urls.defaults import patterns, url
from views import home, score, view_team
urlpatterns = patterns('',
    url(r'^$', home, name='home'),
    url(r'^score/$', score, name='score'),
    url(r'^view_team/(?P<team_id>\d+)/$', view_team, name='view-team'),
)
