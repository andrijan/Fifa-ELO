import operator
import math

from django.db import models
from django.db.models import Q, Count
from datetime import datetime, time, timedelta, date
from compiler import compile

MAX = 32
INITIAL_POINTS = 1500.0

def create_seed_order(bracket_list=[1,2,3,4]):
    if len(bracket_list):
        bracket_size = int(2**math.ceil(math.log(len(bracket_list),2)))
        for i in range(len(bracket_list),bracket_size):
            bracket_list.append(Team.objects.get(name="Steinar"))
    slice = 1
    while slice < len(bracket_list)/2:
        temp = bracket_list
        bracket_list = []
        while len(temp) > 0:
            bracket_list.extend(temp[0:slice])
            del temp[0:slice]
            bracket_list.extend(temp[-slice:])
            del temp[-slice:]
        slice *= 2
    return bracket_list

def F(n):
    if n == 1: return 1
    elif n == 2: return 2
    else: return F(n-1)+2

class FifaTeam(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to="fifa_teams", blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name

class Player(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)

    

    def list_games(self):
        games = Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self]) | Q(away_team__players__in=[self])).order_by('-date').distinct()
        return games

    def count_games(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players=self) | Q(away_team__players=self)).distinct().count()

    def count_wins(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self], result='1') | Q(away_team__players__in=[self], result='2')).distinct().count()

    def count_draws(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self], result='X') | Q(away_team__players__in=[self], result='X')).distinct().count()

    def count_losses(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self], result='2') | Q(away_team__players__in=[self], result='1')).distinct().count()

    def win_loss_ratio(self):
        try:
            return (self.count_wins()+self.count_draws()/2.0) / float(self.count_games())
        except:
            return 0.5

    def win_loss_ratio_percentage(self):
        return self.win_loss_ratio() * 100.0

    def team(self):
        return Team.objects.get(name=self.name, is_2player=False)

    def __unicode__(self):
        return u'%s' % self.name

class Team(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)
    players = models.ManyToManyField(Player)
    is_team = models.BooleanField()
    is_2player = models.BooleanField(default=False)
    image = models.ImageField(upload_to="teams", blank=True, null=True)

    favourite_fifa_team = models.ForeignKey(FifaTeam, blank=True, null=True)

    def find_fifa_team(self):
        home_games = Game.objects.filter(home_team=self).values('home_fifa_team').annotate(Count('home_fifa_team'))
        away_games = Game.objects.filter(away_team=self).values('away_fifa_team').annotate(Count('away_fifa_team'))
        fifa_teams = {}
        for game in home_games:
            fifa_teams[game['home_fifa_team']] = game['home_fifa_team__count']
        for game in away_games:
            try:
                fifa_teams[game['away_fifa_team']] += game['away_fifa_team__count']
            except:
                fifa_teams[game['away_fifa_team']] = game['away_fifa_team__count']

        try:
            fifa_team = FifaTeam.objects.get(pk=max(fifa_teams, key=lambda k: fifa_teams[k]))
        except:
            fifa_team = None

        if not fifa_team == self.favourite_fifa_team:
            self.favourite_fifa_team = fifa_team
            self.save()

    def valid_game(self, team2):
        for player in self.players.all():
            if player in team2.players.all():
                return False
        return True

    def check_achievements(self, game=None, team=None):
        pass

    def get_latest_points(self):
        try:
            return Points.objects.filter(team=self).latest('date').points
        except:
            p = Points(team=self, points=INITIAL_POINTS, date='2012-02-27 12:00:00')
            p.save()
            return p.points

    def get_place(self, date=None):
        teams = Team.objects.filter(is_team=self.is_team)
        if date:
            teams = sorted(teams, key=lambda t: t.get_points_by_date(date).points, reverse=True)
        else:
            teams = sorted(teams, key=lambda t: t.get_latest_points(), reverse=True)
        counter = 1
        for team in teams:
            if team == self:
                return counter
            counter += 1
        return False

    def get_points_by_date(self, date):
        points = self.points_set.filter(game__date__lte=datetime.combine(date, time.max)).order_by('-game__date')
        try:
            return points[0]
        except IndexError:
            return Points.objects.filter(team=self)[0]

    def get_change(self):
        current = self.get_place()
        old = self.get_place(date=date.today() - timedelta(days=1))
        if current < old:
            return "up"
        elif current > old:
            return "down"
        else:
            return "same"

    def get_score_change(self):
        current = self.get_latest_points()
        try:
            old = self.points_set.all().order_by('-date')[1].points
        except:
            return 0.0
        return current - old

    def count_games(self):
        return self.list_home_games().count() + self.list_away_games().count()

    def count_wins(self):
        return self.list_home_games(result='1').count() + self.list_away_games(result='2').count()

    def count_draws(self):
        return self.list_home_games(result='X').count() + self.list_away_games(result='X').count()

    def count_losses(self):
        return self.list_home_games(result='2').count() + self.list_away_games(result='1').count()

    def count_goals(self):
        goals = 0
        for game in self.home_team.filter(result__isnull=False):
            goals += game.home_goals
        for game in self.away_team.filter(result__isnull=False):
            goals += game.away_goals
        return goals

    def count_goals_conceded(self):
        goals = 0
        for game in self.home_team.filter(result__isnull=False):
            goals += game.away_goals
        for game in self.away_team.filter(result__isnull=False):
            goals += game.home_goals
        return goals

    def list_games(self, twoplayer=False):
        twoplayer = self.is_2player
        if not twoplayer:
            games = Game.objects.filter(result__isnull=False).filter(Q(home_team=self) | Q(away_team=self)).order_by('-date')
        else:
            games = TwoPlayerGame.objects.filter(game__result__isnull=False).filter(Q(home_teams__in=[self]) | Q(away_teams__in=[self])).order_by('-game__date').distinct()
            return [game.game for game in games]
        return games

    def list_home_games(self, result=None):
        if self.is_2player:
            games = self.home_teams.filter(game__result__isnull=False).order_by('-date')
            if result:
                games = games.filter(game__result=result)
        else:
            games = self.home_team.filter(result__isnull=False).order_by('-date')
            if result:
                games = games.filter(result=result)
        return games

    def list_away_games(self, result=None):
        if self.is_2player:
            games = self.away_teams.filter(game__result__isnull=False).order_by('-date')
            if result:
                games = games.filter(game__result=result)
        else:
            games = self.away_team.filter(result__isnull=False).order_by('-date')
            if result:
                games = games.filter(result=result)
        return games

    def longest_win_streak(self):
        streak = 0
        current_streak = 0
        for game in self.list_games():
            if game.home_team == self and game.result == "1":
                current_streak += 1
            elif game.away_team == self and game.result =="2":
                current_streak += 1
            else:
                current_streak = 0
            if current_streak > streak:
                streak = current_streak
        return streak

    def longest_losing_streak(self):
        streak = 0
        current_streak = 0
        for game in self.list_games():
            if game.home_team == self and game.result == "2":
                current_streak += 1
            elif game.away_team == self and game.result =="1":
                current_streak += 1
            else:
                current_streak = 0
            if current_streak > streak:
                streak = current_streak
        return streak

    def longest_draw_streak(self):
        streak = 0
        current_streak = 0
        for game in self.list_games():
            if game.home_team == self and game.result == "X":
                current_streak += 1
            elif game.away_team == self and game.result =="X":
                current_streak += 1
            else:
                current_streak = 0
            if current_streak > streak:
                streak = current_streak
        return streak

    def average_goals_per_game(self):
        goals = 0
        for game in self.home_team.filter(result__isnull=False):
            goals += game.home_score
        for game in self.away_team.filter(result__isnull=False):
            goals += game.away_score
        return goals/float(self.count_games())

    def average_goals_conceded_per_game(self):
        goals = 0
        for game in self.home_team.filter(result__isnull=False):
            goals += game.away_score
        for game in self.away_team.filter(result__isnull=False):
            goals += game.home_score
        return goals/float(self.count_games())

    def __unicode__(self):
        if self.name:
            return u'%s' % self.name
        else:
            s = ' og '.join(player.name for player in self.players.all())
            return u'%s' % (s)

RESULT_CHOICES = (
    ('1', '1'),
    ('X', 'X'),
    ('2', '2'),
)

def roundRobin(units, sets=None):
    """ Generates a schedule of "fair" pairings from a list of units """
    if len(units) % 2:
        units.append(None)
    count    = len(units)
    sets     = sets or (count - 1)
    half     = count / 2
    schedule = []
    for turn in range(sets):
        pairings = []
        for i in range(half):
            pairings.append((units[i], units[count-i-1]))
        units.insert(1, units.pop())
        schedule.append(pairings)
    return schedule


class Tournament(models.Model):
    name = models.CharField("Tournament name", max_length=255)
    date = models.DateField("Date of tournament", blank=True, null=True)
    location = models.CharField("Location", max_length=255, blank=True, null=True)
    players = models.ManyToManyField(Player)
    is_team = models.BooleanField(default=True)
    has_groups = models.BooleanField()
    has_double_elimination = models.BooleanField()

    def __unicode__(self):
        return u'%s' % self.name

    def teams(self):
        players = sorted(self.players.all(), key=lambda p: p.team().get_latest_points(), reverse=False)
        teams = []
        if self.is_team:
            while players:
                teams.append(Team.objects.filter(players__in=[players.pop(0)]).get(players__in=[players.pop()]))
        else:
            while players:
                teams.append(Team.objects.get(players__in=[players.pop()], is_2player=False, is_team=False))
        teams = create_seed_order(teams)
        return teams


    def clean(self, *args, **kwargs):
        super(Tournament, self).save(*args, **kwargs)
        teams = self.teams()
        if self.has_groups:
            try:
                group = TournamentGroup.objects.get(name="Group A", tournament=self)
            except:
                group = TournamentGroup(name="Group A", tournament=self)
                group.save()
            for round_num in roundRobin(teams):
                for g in round_num:
                    if g[0] is not None and g[1] is not None:
                        game = Game(home_team=g[0], away_team=g[1], tournament=self)
                        game.save()
                        group.games.add(game)
                        group.save()
        elif self.has_double_elimination:
            ctr = 1
            old_team = None
            for team in teams:
                if ctr % 2 == 0:
                    game = Game(home_team=old_team, away_team=team, tournament=self, tournament_code='W1G' + str(ctr/2))
                    game.save()
                else:
                    old_team = team
                ctr += 1


class Game(models.Model):
    home_team = models.ForeignKey(Team, related_name="home_team", blank=True, null=True)
    away_team = models.ForeignKey(Team, related_name="away_team", blank=True, null=True)
    home_fifa_team = models.ForeignKey(FifaTeam, related_name="home_fifa_team", blank=True, null=True)
    away_fifa_team = models.ForeignKey(FifaTeam, related_name="away_fifa_team", blank=True, null=True)
    date = models.DateTimeField("Date of game", auto_now_add=True)
    result = models.CharField("Result", max_length=1, choices=RESULT_CHOICES, blank=True, null=True)
    home_score = models.IntegerField(blank=True, null=True)
    away_score = models.IntegerField(blank=True, null=True)
    date_played = models.DateTimeField("Playtime of game", auto_now=True, blank=True, null=True)
    tournament = models.ForeignKey(Tournament, blank=True, null=True)
    tournament_code = models.CharField(max_length=255, blank=True, null=True)
    calculate_points = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s: %s - %s' % (self.date, self.home_team, self.away_team)

    def display_score(self):
        if self.result:
            return u'%s - %s' % (self.home_score, self.away_score)
        else:
            return None

    def winner(self):
        if self.result == "1":
            return self.home_team
        elif self.result == "2":
            return self.away_team
        return None

    def loser(self):
        if self.result == "2":
            return self.home_team
        elif self.result == "1":
            return self.away_team
        return None

    def eliminiation_game(self):
        if self.tournamentelimination_set.all().count() > 0:
            return self.tournamentelimination_set.all()[0]
        else:
            return False

    def num_first_round_games(self):
        return Game.objects.filter(tournament=self.tournament, tournament_code__startswith='W1').count()

    def check_achievements(self, team=None):
        for template in AchievementTemplate.objects.all():
            pred = template.predicate.replace('\r','')
            code = compile(pred, '<string>', 'exec')
            ns = {}
            exec code in ns
            team1 = self.home_team
            team2 = self.away_team
            for team in team1,team2:
                try:
                    achievement = Achievement.objects.get(template=template, team=team)
                except:
                    achievement = Achievement(template=template, team=team, points=0)
                    achievement.save()
                changed, new_points = ns['match'](self, team, achievement.points)
                if template.is_average:
                    achievement.game.clear()
                    achievement.game.add(self)
                    achievement.points = new_points
                    achievement.save()
                elif changed:
                    if float(new_points) > float(achievement.points):
                        achievement.game.clear()
                        achievement.points = new_points
                    achievement.game.add(self)
                    achievement.save()

    def save(self, *args, **kwargs):
        if self.tournament and self.result:
            code = list(self.tournament_code)
            bracket = code[0]
            b_round = code[1]
            b_game= code[3]
            num_games = self.num_first_round_games()
            if bracket == 'W':
                new_bracket = 'L'
                if int(b_round) % 2 == 0:
                    game_list = range(1,(num_games / int(b_round))+1)
                    reverse_game_list = list(reversed(game_list))
                    z = dict(zip(game_list, reverse_game_list))
                    new_game = str(z[int(b_game)])
                else:
                    new_game = str((int(b_game)+1)/2)
                new_round = str(F(int(b_round)))
                game, created = Game.objects.get_or_create(tournament=self.tournament, tournament_code=new_bracket + new_round + 'G' + new_game)
                game.away_team = self.loser()
                game.save()
                new_game = str((int(b_game)+1)/2)
            else:
                if int(b_round) % 2 == 0:
                    new_game = str((int(b_game)+1)/2)
                else:
                    new_game = b_game
            game, created = Game.objects.get_or_create(tournament=self.tournament, tournament_code=bracket + str(int(b_round)+1) + 'G' + new_game)
            if int(b_round) % 2 != 0 and bracket == 'L':
                game.home_team = self.winner()
            elif int(b_game) % 2 == 0:
                game.away_team = self.winner()
            elif int(b_game) % 2 != 0:
                game.home_team = self.winner()
            game.save()
            print game


        if self.calculate_points and Points.objects.filter(game=self).count() == 0:
            if self.result == '1':
                result = 1
            elif self.result == 'X':
                result = 0.5
            else:
                result = 0

            if self.home_team.count_games() <= 30:
                home_k_value = 32
            elif self.home_team.count_games() <= 100:
                home_k_value = 24
            else:
                if self.home_team.get_latest_points() < 1650:
                    home_k_value = 16
                elif self.home_team.get_latest_points() < 1800:
                    home_k_value = 12
                else:
                    home_k_value = 10

            if self.away_team.count_games() <= 30:
                away_k_value = 32
            elif self.away_team.count_games() <= 100:
                away_k_value = 24
            else:
                if self.away_team.get_latest_points() < 1650:
                    away_k_value = 16
                elif self.away_team.get_latest_points() < 1800:
                    away_k_value = 12
                else:
                    away_k_value = 10

            p1 = self.home_team.get_latest_points()
            p2 = self.away_team.get_latest_points()
            e1 = 1/(1+10**((p2-p1)/400))
            e2 = 1/(1+10**((p1-p2)/400))
            p1new = p1+home_k_value*(result-e1)
            p2new = p2+away_k_value*(1-result-e2)
            np1 = Points(team=self.home_team,points=p1new)
            np1.save()
            np2 = Points(team=self.away_team,points=p2new)
            np2.save()

        super(Game, self).save(*args, **kwargs)
        try:
            np1.game = self
            np1.save()
        except:
            pass
        try:
            np2.game = self
            np2.save()
        except:
            pass
        if self.calculate_points:
            self.check_achievements()

        if self.result:
            self.home_team.find_fifa_team()
            self.away_team.find_fifa_team()

            if self.home_team.is_team:
                TwoPlayerGame.objects.create(game=self)

class TwoPlayerGame(models.Model):
    game = models.ForeignKey(Game)
    home_teams = models.ManyToManyField(Team, related_name="home_teams")
    away_teams = models.ManyToManyField(Team, related_name="away_teams")

    def __unicode__(self):
        return u'%s - 2 player' % self.game

    def home_team(self):
        return Team.objects.filter(players__in=[self.home_teams.all()[0].players.all()[0]]).get(players__in=[self.home_teams.all()[1].players.all()[0]])

    def save(self, *args, **kwargs):
        super(TwoPlayerGame, self).save(*args, **kwargs)
        for p in self.game.home_team.players.all():
            team, created = Team.objects.get_or_create(name=p.name, is_2player=True)
            if created:
                team.players.add(p)
                team.save()
            self.home_teams.add(team)
        for p in self.game.away_team.players.all():
            team, created = Team.objects.get_or_create(name=p.name, is_2player=True)
            if created:
                team.players.add(p)
                team.save()
            self.away_teams.add(team)
        combo1_ave = sum(t.get_latest_points() for t in self.home_teams.all()) / self.home_teams.all().count()
        combo2_ave = sum(t.get_latest_points() for t in self.away_teams.all()) / self.home_teams.all().count()
        if self.game.result == '1':
            result = 1
        elif self.game.result == 'X':
            result = 0.5
        else:
            result = 0
        e1 = 1/(1+10**((combo2_ave-combo1_ave)/400))
        e2 = 1/(1+10**((combo1_ave-combo2_ave)/400))


        t1 = self.home_teams.all()[0]
        t2 = self.home_teams.all()[1]
        t3 = self.away_teams.all()[0]
        t4 = self.away_teams.all()[1]

        for team in [t1,t2]:
            if team.count_games() <= 30:
                team_k_value = 32
            elif team.count_games() <= 100:
                team_k_value = 24
            else:
                if team.get_latest_points() < 1650:
                    team_k_value = 16
                elif team.get_latest_points() < 1800:
                    team_k_value = 12
                else:
                    team_k_value = 10
            team_points = team_k_value*(result-e1)
            team_points_new = team.get_latest_points() + team_points
            np = Points(team=team, points=team_points_new, game=self.game)
            np.save()

        for team in [t3,t4]:
            if team.count_games() <= 30:
                team_k_value = 32
            elif team.count_games() <= 100:
                team_k_value = 24
            else:
                if team.get_latest_points() < 1650:
                    team_k_value = 16
                elif team.get_latest_points() < 1800:
                    team_k_value = 12
                else:
                    team_k_value = 10
            team_points = team_k_value*(1-result-e2)
            team_points_new = team.get_latest_points() + team_points
            np = Points(team=team, points=team_points_new, game=self.game)
            np.save()
        """
        team1_points = 32*(result-e1)
        team2_points = 32*(1-result-e2)

        team1_e = 1/(1+10**((t1.get_latest_points()-t2.get_latest_points())/400))
        p1new = t1.get_latest_points() + team1_points*team1_e
        p2new = t2.get_latest_points() + team1_points*(1-team1_e)
        team2_e = 1/(1+10**((t3.get_latest_points()-t4.get_latest_points())/400))
        p3new = t3.get_latest_points() + team2_points*team2_e
        p4new = t4.get_latest_points() + team2_points*(1-team2_e)

        np1 = Points(team=t1,points=p1new, game=self.game)
        np1.save()
        np2 = Points(team=t2,points=p2new, game=self.game)
        np2.save()
        np3 = Points(team=t3,points=p3new, game=self.game)
        np3.save()
        np4 = Points(team=t4,points=p4new, game=self.game)
        np4.save()
        """

class TournamentGroup(models.Model):
    name = models.CharField("Group name", max_length=255)
    tournament = models.ForeignKey(Tournament)
    games = models.ManyToManyField(Game)

    def __unicode__(self):
        return u'%s - %s' % (self.tournament.name, self.name)

    def calculate_places(self):
        teams = {}
        for game in self.games.all():
            if game.result == "1":
                try:
                    teams[game.home_team] = teams[game.home_team] + 3
                except:
                    teams[game.home_team] = 3
            elif game.result == "X":
                try:
                    teams[game.home_team] = teams[game.home_team] + 1
                except:
                    teams[game.home_team] = 1
                try:
                    teams[game.away_team] = teams[game.away_team] + 1
                except:
                    teams[game.away_team] = 1
            elif game.result == "2":
                try:
                    teams[game.away_team] = teams[game.away_team] + 3
                except:
                    teams[game.away_team] = 3
        teams = sorted(teams.iteritems(), key=operator.itemgetter(1), reverse=True)
        import math
        num_teams = int(2**(math.floor(math.log(len(teams),2))))
        return teams[0:num_teams]

    def add_to_elimination(self):
        teams = self.calculate_places()
        code = len(teams)

        while teams:
            game = Game(home_team=teams.pop(0)[0], away_team=teams.pop()[0], tournament=self.tournament)
            game.save()
            te = TournamentElimination(game=game, status=EliminationStatus.objects.get(code=code))
            te.save()

        return True

class EliminationStatus(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField()

    def __unicode__(self):
        return u'%s' % self.name

class TournamentElimination(models.Model):
    game = models.ForeignKey(Game)
    status = models.ForeignKey(EliminationStatus)
    double = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s - %s' % (self.game, self.status.name)

class AchievementTemplate(models.Model):
    name = models.CharField("Achievement name", max_length=255, blank=True, null=True)
    icon = models.ImageField(upload_to="achievements")
    predicate = models.TextField(null=True, blank=True)
    is_average = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % (self.name)

class Achievement(models.Model):
    team = models.ForeignKey(Team, blank=True, null=True)
    game = models.ManyToManyField(Game, blank=True, null=True)
    points = models.FloatField(blank=True, null=True)
    template = models.ForeignKey(AchievementTemplate, blank=True, null=True)

    def is_highest(self):
        achievements = Achievement.objects.filter(template=self.template, team__is_team=self.team.is_team)
        for a in achievements:
            if a.points > self.points:
                return False
        return True

    def __unicode__(self):
        return u'%s : %s' % (self.template.name, self.team.name)

class Points(models.Model):
    team = models.ForeignKey(Team)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    points = models.FloatField("Elo stig")
    game = models.ForeignKey(Game, null=True, blank=True)

    def get_change(self):
        return self.points - Points.objects.filter(team=self.team).filter(date__lt=self.date).order_by('-date')[0].points

    def __unicode__(self):
        return u'%s: %s - %s' % (self.date, self.team, self.points)


