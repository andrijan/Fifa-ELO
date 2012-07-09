from django.conf.urls.defaults import patterns, url
from django.views.generic import list_detail

from models import Game

from views import home, score, view_team, view_player, achievements, all_teams, all_games, generate_teams, calculate_results, compare_teams, compare_players, view_tournament, list_tournaments, next_elimination_stage, game_combinations, play_tournament_matches, game_form
urlpatterns = patterns('',
    url(r'^$', home, name='home'),
    url(r'^score/$', score, name='score'),
    url(r'^achievements/$', achievements, name='achievements'),
    url(r'^generate_teams/$', generate_teams, name='generate-teams'),
    url(r'^compare_teams/$', compare_teams, name='compare-teams'),
    url(r'^compare_players/$', compare_players, name='compare-players'),
    url(r'^game_combinations/$', game_combinations, name='game-combinations'),
    url(r'^all_teams/$', all_teams, name='all-teams'),
    url(r'^all_games/$', all_games, name='all-games'),
    url(r'^calculate_results/$', calculate_results, name='calculate-results'),
    url(r'^view_team/(?P<team_id>\d+)/$', view_team, name='view-team'),
    url(r'^view_player/(?P<player_id>\d+)/$', view_player, name='view-player'),
    url(r'^view_tournament/(?P<tournament_id>\d+)/$', view_tournament, name='view-tournament'),
    url(r'^list_tournaments/$', list_tournaments, name='list-tournaments'),
    url(r'^next_elimination_stage/(?P<tournament_id>\d+)/(?P<current_code>\d+)/$', next_elimination_stage, name='next-elimination-stage'),
    url(r'^next_elimination_stage/(?P<tournament_id>\d+)/$', next_elimination_stage, name='next-elimination-stage'),

    url(r'^game/form/(?P<game_id>\d+)/$', game_form, name='game-form'),
    url(r'^game/form/$', game_form, name='game-form'),

    url(r'^view_game/(?P<object_id>\d+)/$', list_detail.object_detail, {'queryset': Game.objects.all(), 'template_name': 'core/view_game.html'}, name='view-game'),
    url(r'^fix_tournament/(?P<tournament_id>\d+)/$', play_tournament_matches, name='play-tournament-matches'),
)
