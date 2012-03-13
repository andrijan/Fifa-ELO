# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext


import json

from models import Team, Points, Player, Game

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

def all_teams(request):
    is_team = request.GET.get('is_team', False)
    teams = Team.objects.filter(is_team=is_team)
    dates = Points.objects.all().dates('game__date', 'day')
    points = []
    for date in dates:
        current_date = {'date': date}
        current_teams = []
        for team in teams:
            current_teams.append([team, team.get_points_by_date(date).points])
        current_date['teams'] = current_teams
        points.append(current_date)
    ctx = {'teams': teams, 'dates': dates, 'points': points}
    return render_to_response('core/all_teams.html', ctx,
                                context_instance=RequestContext(request))

def achievements(request):
    games = Game.objects.all()
    bw = 0
    winner = None
    for game in games:
        if abs(game.home_score - game.away_score) > bw:
            bw = abs(game.home_score - game.away_score)
            winner = game
    ctx = {'winner': winner}
    return render_to_response('core/achievements.html', ctx,
                              context_instance=RequestContext(request))


def home(request):
    teams = Team.objects.filter(is_team=True)
    players = Team.objects.filter(is_team=False)
    combined = Player.objects.all()
    teams = sorted(teams, key=lambda t: t.get_latest_points(), reverse=True)
    players = sorted(players, key=lambda t: t.get_latest_points(), reverse=True)
    combined = sorted(combined, key=lambda p: p.win_loss_ratio(), reverse=True)
    points = Points.objects.all()
    ctx = {'teams': teams, 'players': players, 'points': points, 'combined': combined}
    return render_to_response('core/homepage.html', ctx,
                              context_instance=RequestContext(request))
