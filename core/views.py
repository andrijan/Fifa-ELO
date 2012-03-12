# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext


import json

from models import Team, Points, Player

def score(request):
    teams = Team.objects.all()
    if 'is_team' in request.GET:
        is_team = request.GET.get('is_team', 'false') == 'true'
        teams = teams.filter(is_team=is_team)
    points = []
    for team in teams:
        points.append({'team': team.name,'points':team.get_latest_points()})

    ordered_points = sorted(points, key=lambda k: k['points'], reverse=True)

    #data = serializers.serialize('json', points)
    return HttpResponse(json.dumps(ordered_points))

def view_team(request, team_id):
    team = Team.objects.get(pk=team_id)
    return render_to_response('core/view_team.html', {'team': team},
                              context_instance=RequestContext(request))

def view_player(request, player_id):
    player = Player.objects.get(pk=player_id)
    team = Team.objects.get(name=player.name)
    return render_to_response('core/view_player.html', {'player': player, 'team': team},
                              context_instance=RequestContext(request))

"""
def all_teams(request):
    teams = Team.objects.all()
    dates = Points.objects.all().dates('game__date', 'day')
"""

def home(request):
    teams = Team.objects.filter(is_team=True)
    players = Team.objects.filter(is_team=False)
    teams = sorted(teams, key=lambda t: t.get_latest_points(), reverse=True)
    players = sorted(players, key=lambda t: t.get_latest_points(), reverse=True)
    points = Points.objects.all()
    ctx = {'teams': teams, 'players': players, 'points': points}
    return render_to_response('core/homepage.html', ctx,
                              context_instance=RequestContext(request))
