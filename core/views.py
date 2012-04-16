# -*- coding: utf-8 -*-
from django.db.models import Q
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import defaultdict

import json

from models import Team, Points, Player, Game, Achievement, Tournament, TournamentElimination, EliminationStatus, TournamentGroup

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
    
    achievements_by_template = defaultdict(list)
    for achievement in achievements:
        try:
            game = achievement.game.all().reverse()[0]
        except:
            game = None
        achievements_by_template[achievement.template].append((achievement.team.name, achievement.points, game))
    for k in achievements_by_template.iterkeys():
        achievements_by_template[k] = sorted(achievements_by_template[k], key=lambda listIn: listIn[1], reverse=True)

    ctx = {'achievements': achievements, 'achievements_by_template': achievements_by_template.items()}
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

    total_games = 9999999
    teamA = None
    teamB = None
    for game in valid_games:
        team1 = Team.objects.filter(players=game[0][0]).get(players=game[0][1])
        team2 = Team.objects.filter(players=game[1][0]).get(players=game[1][1])
        num_games = Game.objects.filter(Q(home_team=team1, away_team=team2) | Q(home_team=team2, away_team=team1)).count() #team1.count_games() + team2.count_games()
        if num_games < total_games:
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

def compare_p(player1, player2):
    games = player1.list_games().filter(Q(home_team__players__in=[player2], away_team__players__in=[player1]) | Q(away_team__players__in=[player2], home_team__players__in=[player1]))
    t1win = 0
    draw = 0
    t2win = 0
    t1points = 0.0
    t2points = 0.0
    for game in games:
        p1 = Points.objects.get(game=game, team__players__in=[player1])
        p2 = Points.objects.get(game=game, team__players__in=[player2])
        if game.result == "X":
            draw += 1
        elif player1 in game.home_team.players.all():
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

def compare_players(request):
    player1 = request.GET.get('player1', '')
    player2 = request.GET.get('player2', '')
    player1 = Player.objects.get(pk=player1)
    player2 = Player.objects.get(pk=player2)
    t1win, draw, t2win, t1points, t2points = compare_p(player1, player2)

    ctx = {'t1win': t1win,
            't2win': t2win,
            'draw' : draw,
            't1points' : t1points,
            't2points' : t2points,
            'player1' : player1,
            'player2' : player2,
    }

    return render_to_response('core/compare_players.html', ctx,
                                context_instance=RequestContext(request))

def view_tournament(request, tournament_id):
    tournament = Tournament.objects.get(pk=tournament_id)
    ctx = {'tournament': tournament,
    }

    return render_to_response('core/view_tournament.html', ctx,
                                context_instance=RequestContext(request))

def list_tournaments(request):
    tournaments = Tournament.objects.all()
    ctx = {'tournaments': tournaments,
    }

    return render_to_response('core/list_tournaments.html', ctx,
                                context_instance=RequestContext(request))

def next_elimination_stage(request, tournament_id, current_code=None):
    tournament = Tournament.objects.get(pk=tournament_id)
    if not current_code:
        tg = TournamentGroup.objects.filter(tournament=tournament)[0]
        tg.add_to_elimination()
        return HttpResponseRedirect(reverse('view-tournament', args=[tournament_id]))

    tes = list(TournamentElimination.objects.filter(game__tournament=tournament, status__code=current_code))
    new_code = EliminationStatus.objects.get(code=(int(current_code) / 2))
    while tes:
        game = Game(home_team=tes.pop(0).game.winner(), away_team=tes.pop().game.winner(), tournament=tournament)
        game.save()
        te = TournamentElimination(game=game, status=new_code)
        te.save()

    return HttpResponseRedirect(reverse('view-tournament', args=[tournament_id]))

def game_combinations(request):
    is_team = request.GET.get('is_team', False)
    teams = Team.objects.filter(is_team=is_team)
    list_teams = {}
    for team1 in teams:
        for team2 in teams:
            if team1.valid_game(team2):
                try:
                    list_teams[(team2, team1)]
                except:
                    t1,t2,t3,p1,p2 = compare(team1, team2)
                    list_teams[(team1,team2)] = t1+t2+t3

    list_teams = sorted(list_teams.items(), key=lambda (k,v): (v,k))
    ctx = {'list_teams': list_teams,
    }

    return render_to_response('core/game_combinations.html', ctx,
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
