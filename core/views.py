# -*- coding: utf-8 -*-
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import json

from models import Team, Points, Player, Game, Achievement

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

def all_games(request):
    game_list = Game.objects.all().order_by('-date')
    paginator = Paginator(game_list, 15) # Show 15 games per page

    page = request.GET.get('page', 1)

    try:
        games = paginator.page(page)
    except PageNotAnInteger:
        games = paginator.page(1)
    except EmptyPage:
        games = paginator.page(paginator.num_pages)

    ctx = {'games': games}
    return render_to_response('core/all_games.html', ctx,
                                context_instance=RequestContext(request))


def achievements(request):
    achievements = Achievement.objects.all()
    ctx = {'achievements': achievements}
    return render_to_response('core/achievements.html', ctx,
                              context_instance=RequestContext(request))

def generate_teams(request):
    import itertools
    players = request.GET.get('players', '')
    players = players.split(',')
    ps = []
    for player in players:
        ps.append(Player.objects.get(pk=player))
    comb = itertools.combinations(ps,2)
    games = itertools.combinations(comb,2)
    valid_games = []
    for g in games:
        valid = True
        team1 = g[0]
        team2 = g[1]
        for p in team1:
            if p in team2:
                valid = False
        if valid:
            valid_games.append(g)

    total_games = None
    teamA = None
    teamB = None
    for game in valid_games:
        team1 = Team.objects.filter(players=game[0][0]).get(players=game[0][1])
        team2 = Team.objects.filter(players=game[1][0]).get(players=game[1][1])
        num_games = team1.count_games() + team2.count_games()
        if not total_games or num_games < total_games:
            total_games = num_games
            teamA = team1
            teamB = team2

    ctx = {'team1': teamA, 'team2': teamB, 'total_games': total_games}
    return render_to_response('core/generate_teams.html', ctx,
                              context_instance=RequestContext(request))

def calculate(points1, points2, result):
    e1 = 1/(1+10**((points2-points1)/400))
    e2 = 1/(1+10**((points1-points2)/400))
    return 32*(result-e1), 32*(1-result-e2)

def calculate_results(request):
    team1 = request.GET.get('team1', '')
    team2 = request.GET.get('team2', '')
    team1 = Team.objects.get(pk=team1)
    team2 = Team.objects.get(pk=team2)

    p1 = team1.get_latest_points()
    p2 = team2.get_latest_points()

    t1win1, t2win1 = calculate(p1, p2, 1)
    t1draw, t2draw = calculate(p1, p2, 0.5)
    t1win2, t2win2 = calculate(p1, p2, 0)

    ctx = { 'team1': team1,
            'team2': team2,
            't1win1': t1win1,
            't2win1': t2win1,
            't1win2': t1win2,
            't2win2': t2win2,
            't1draw': t1draw,
            't2draw': t2draw
    }
    return render_to_response('core/calculate_results.html', ctx,
                                context_instance=RequestContext(request))

def compare(team1, team2):
    games = team1.list_games().filter(Q(home_team=team2) | Q(away_team=team2))
    t1win = 0
    draw = 0
    t2win = 0
    t1points = 0.0
    t2points = 0.0
    for game in games:
        p1 = Points.objects.get(game=game, team=team1)
        p2 = Points.objects.get(game=game, team=team2)
        if game.result == "X":
            draw += 1
        elif game.home_team == team1:
            if game.result == "1":
                t1win += 1
            elif game.result == "2":
                t2win += 1
        else:
            if game.result == "2":
                t1win += 1
            elif game.result == "1":
                t2win += 1
        t1points += p1.get_change()
        t2points += p2.get_change()
    return t1win, draw, t2win, t1points, t2points

def compare_teams(request):
    team1 = request.GET.get('team1', '')
    team2 = request.GET.get('team2', '')
    team1 = Team.objects.get(pk=team1)
    team2 = Team.objects.get(pk=team2)
    t1win, draw, t2win, t1points, t2points = compare(team1, team2)

    ctx = {'t1win': t1win,
            't2win': t2win,
            'draw' : draw,
            't1points' : t1points,
            't2points' : t2points,
            'team1' : team1,
            'team2' : team2,
    }

    return render_to_response('core/compare_teams.html', ctx,
                                context_instance=RequestContext(request))


def home(request):
    teams = Team.objects.filter(is_team=True)
    players = Team.objects.filter(is_team=False)
    combined = Player.objects.all()
    if 'no_empty' in request.GET:
        for player in players:
            if player.count_games() == 0:
                players = players.exclude(pk=player.pk)
        for player in combined:
            if player.count_games() == 0:
                combined = combined.exclude(pk=player.pk)
        for team in teams:
            if team.count_games() == 0:
                teams = teams.exclude(pk=team.pk)
    teams = sorted(teams, key=lambda t: t.get_latest_points(), reverse=True)
    players = sorted(players, key=lambda t: t.get_latest_points(), reverse=True)
    combined = sorted(combined, key=lambda p: p.win_loss_ratio(), reverse=True)
    points = Points.objects.all() 
    ctx = {'teams': teams, 'players': players, 'points': points, 'combined': combined}
    return render_to_response('core/homepage.html', ctx,
                              context_instance=RequestContext(request))
