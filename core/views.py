# -*- coding: utf-8 -*-
from django.db.models import Q
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from collections import defaultdict

import json

from models import Team, Points, Player, Game, Achievement, Tournament, TournamentElimination, EliminationStatus, TournamentGroup, TeamTableSnapshot, PlayerTableSnapshot, GameForm

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
    game_list = team.list_games(team.is_2player)

    paginator = Paginator(game_list, 15)
    page = request.GET.get('page', 1)

    try:
        games = paginator.page(page)
    except PageNotAnInteger:
        games = paginator.page(1)
    except EmptyPage:
        games = paginator.page(paginator.num_pages)

    ctx = {'team': team, 'games': games}
    return render_to_response('core/view_team.html', ctx,
                              context_instance=RequestContext(request))

def view_player(request, player_id):
    player = Player.objects.get(pk=player_id)
    team = Team.objects.get(name=player.name)
    game_list = player.list_games()

    paginator = Paginator(game_list, 15)
    page = request.GET.get('page', 1)

    try:
        games = paginator.page(page)
    except PageNotAnInteger:
        games = paginator.page(1)
    except EmptyPage:
        games = paginator.page(paginator.num_pages)

    ctx = {'player': player, 'team': team, 'games': games}
    return render_to_response('core/view_player.html', ctx,
                              context_instance=RequestContext(request))

def all_teams(request):
    is_team = request.GET.get('is_team', False)
    teams = Team.objects.filter(is_team=is_team, is_2player=False)
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
    games = Game.objects.filter(tournament=tournament, tournament_code__startswith='W1')
    if tournament.has_double_elimination and games.count() > 0:
        teams = []
        for game in games:
            teams.append(game.home_team)
            teams.append(game.away_team)
        #teams = tournament.teams()
        tuple_teams = []
        ctr = 1
        old_team = ''
        for team in teams:
            if ctr % 2 == 0:
                tuple_teams.append([old_team, team])
            else:
                old_team = team
            ctr += 1
        results_w, results_l, results_f = [],[],[]
        games = Game.objects.filter(tournament=tournament).order_by('tournament_code')
        for game in games:
            if list(game.tournament_code)[0] == 'W':
                results_w.append({'home_score': game.home_score, 'away_score': game.away_score, 'round_num': list(game.tournament_code)[1], 'result':game.result})
            elif list(game.tournament_code)[0] == 'L':
                results_l.append({'home_score': game.home_score, 'away_score': game.away_score, 'round_num': list(game.tournament_code)[1], 'result':game.result})
            else:
                results_f.append({'home_score': game.home_score, 'away_score': game.away_score, 'round_num': list(game.tournament_code)[1], 'result':game.result})
        ctx = {'tournament': tournament,
                'teams': tuple_teams,
                'results_w': results_w,
                'results_l': results_l,
                'results_f': results_f,
        }
    if tournament.has_groups:
        groups = TournamentGroup.objects.filter(tournament=tournament)
        g = {}
        for group in groups:
            d = {}
            for game in group.games.all():
                d[game.home_team] = {} if game.home_team not in d else d[game.home_team]
                d[game.away_team] = {} if game.away_team not in d else d[game.away_team]
                d[game.home_team]['games'] = 0 if 'games' not in d else d[game.home_team]['games']
                d[game.away_team]['games'] = 0 if 'games' not in d else d[game.away_team]['games']
                d[game.home_team]['wins'] = 0 if 'wins' not in d else d[game.home_team]['wins']
                d[game.away_team]['wins'] = 0 if 'wins' not in d else d[game.away_team]['wins']
                d[game.home_team]['draws'] = 0 if 'draws' not in d else d[game.home_team]['draws']
                d[game.away_team]['draws'] = 0 if 'draws' not in d else d[game.away_team]['draws']
                d[game.home_team]['losses'] = 0 if 'losses' not in d else d[game.home_team]['losses']
                d[game.away_team]['losses'] = 0 if 'losses' not in d else d[game.away_team]['losses']
                d[game.home_team]['plus'] = 0 if 'plus' not in d else d[game.home_team]['plus']
                d[game.away_team]['plus'] = 0 if 'plus' not in d else d[game.away_team]['plus']
                d[game.home_team]['minus'] = 0 if 'minus' not in d else d[game.home_team]['minus']
                d[game.away_team]['minus'] = 0 if 'minus' not in d else d[game.away_team]['minus']
                d[game.home_team]['points'] = 0 if 'points' not in d else d[game.home_team]['points']
                d[game.away_team]['points'] = 0 if 'points' not in d else d[game.away_team]['points']
                if game.result:
                    d[game.home_team]['games'] = d[game.home_team]['games'] + 1 if 'games' in d[game.home_team] else 1
                    d[game.away_team]['games'] = d[game.away_team]['games'] + 1 if 'games' in d[game.away_team] else 1
                    d[game.home_team]['plus'] = d[game.home_team]['plus'] +  game.home_score if 'plus' in d[game.home_team] else game.home_score
                    d[game.away_team]['plus'] = d[game.away_team]['plus'] + game.away_score if 'plus' in d[game.away_team] else game.away_score
                    d[game.home_team]['minus'] = d[game.home_team]['minus'] + game.away_score if 'minus' in d[game.home_team] else game.away_score
                    d[game.away_team]['minus'] = d[game.away_team]['minus'] + game.home_score if 'minus' in d[game.away_team] else game.home_score
                    if game.winner() == game.home_team:
                        d[game.home_team]['points'] = d[game.home_team]['points'] + 3 if 'points' in d[game.home_team] else 3
                        d[game.home_team]['wins'] = d[game.home_team]['wins'] + 1 if 'wins' in d[game.home_team] else 1
                        d[game.away_team]['losses'] = d[game.away_team]['losses'] + 1 if 'losses' in d[game.away_team] else 1
                    elif game.winner() == game.away_team:
                        d[game.away_team]['points'] = d[game.away_team]['minus'] + 3 if 'points' in d[game.away_team] else 3
                        d[game.home_team]['losses'] = d[game.home_team]['losses'] + 1 if 'losses' in d[game.home_team] else 1
                        d[game.away_team]['wins'] = d[game.away_team]['wins'] + 1 if 'wins' in d[game.away_team] else 1
                    else:
                        d[game.home_team]['draws'] = d[game.home_team]['draws'] + 1 if 'draws' in d[game.home_team] else 1
                        d[game.away_team]['draws'] = d[game.away_team]['draws'] + 1 if 'draws' in d[game.away_team] else 1
            g[group.name] = d

        ctx = {'tournament': tournament,
                'groups': g}

    return render_to_response('core/view_tournament.html', ctx,
                                context_instance=RequestContext(request))

def play_tournament_matches(request, tournament_id):
    tournament = Tournament.objects.get(pk=tournament_id)
    steinar = Team.objects.get(name="Steinar")
    games = Game.objects.filter(tournament=tournament, home_team=steinar, away_team__isnull=False, result__isnull=True)
    for game in games:
        game.result = "2"
        game.home_score = 0
        game.away_score = 1
        game.save()
    games = Game.objects.filter(tournament=tournament, away_team=steinar, home_team__isnull=False, result__isnull=True)
    for game in games:
        game.result = "1"
        game.home_score = 1
        game.away_score = 0
        game.save()
    return HttpResponseRedirect(reverse('view-tournament', args=[tournament_id]))

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

    new_code = EliminationStatus
    if tournament.has_double_elimination:
        tes = list(TournamentElimination.objects.filter(game__tournament=tournament, status__code__startswith=current_code))
        while tes:
            first_game = tes.pop(0).game
            second_game = tes.pop(0).game
            if list(current_code)[0] == "W":
                te = TournamentElimination.objects.get_or_create(game__tournament=tournament, status=list(current_code)[0] + str(int(list(current_code)[1]) + 1))
                game = Game(home_team=first_game.loser(), away_team=second_game.loser(), tournament=tournament)
                game.save()
                te = TournamentElimination(game=game, status='L' + list(current_code)[1])
                te.save()
    else:
        tes = list(TournamentElimination.objects.filter(game__tournament=tournament, status__code=current_code))
        new_code = EliminationStatus.objects.get(code=(int(current_code) / 2))
        while tes:
            first_game = tes.pop(0).game
            second_game = tes.pop(0).game
            game = Game(home_team=first_game.winner(), away_team=second_game.winner(), tournament=tournament)
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

def game_form(request, game_id=None):
    if request.method == "POST":
        form = GameForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('home'))
    else:
        if game_id:
            game = Game.objects.get(pk=game_id)
            form = GameForm(instance=game)
        else:
            form = GameForm()

    return render_to_response('core/game_form.html', {'form': form},
                                context_instance=RequestContext(request))


def home(request):
    """
    teams = Team.objects.filter(is_team=True, is_2player=False)
    twoplayers = Team.objects.filter(is_2player=True)
    players = Team.objects.filter(is_team=False, is_2player=False)
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
    twoplayers = sorted(twoplayers, key=lambda t: t.get_latest_points(), reverse=True)
    players = sorted(players, key=lambda t: t.get_latest_points(), reverse=True)
    combined = sorted(combined, key=lambda p: p.win_loss_ratio(), reverse=True)
    points = Points.objects.all() 
    """
    teams = TeamTableSnapshot.objects.filter(is_team=True, is_2player=False).order_by('-points')
    twoplayers = TeamTableSnapshot.objects.filter(is_2player=True).order_by('-points')
    players = TeamTableSnapshot.objects.filter(is_team=False, is_2player=False).order_by('-points')
    combined = PlayerTableSnapshot.objects.all().order_by('-ratio')
    ctx = {'teams': teams, 'players': players, 'combined': combined, 'twoplayers': twoplayers}
    return render_to_response('core/homepage.html', ctx,
                              context_instance=RequestContext(request))
