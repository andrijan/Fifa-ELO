import operator

from django.db import models
from django.db.models import Q
from datetime import datetime, time, timedelta, date
from compiler import compile

MAX = 32
INITIAL_POINTS = 1500.0

class FifaTeam(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name

class Player(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)

    def list_games(self):
        games = Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self]) | Q(away_team__players__in=[self])).order_by('-date').distinct()
        return games

    def count_games(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players=self) | Q(away_team__players=self)).order_by('-date').distinct().count()

    def count_wins(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self], result='1') | Q(away_team__players__in=[self], result='2')).order_by('-date').distinct().count()

    def count_draws(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self], result='X') | Q(away_team__players__in=[self], result='X')).order_by('-date').distinct().count()

    def count_losses(self):
        return Game.objects.filter(result__isnull=False).filter(Q(home_team__players__in=[self], result='2') | Q(away_team__players__in=[self], result='1')).order_by('-date').distinct().count()

    def win_loss_ratio(self):
        try:
            return (self.count_wins()+self.count_draws()/2.0) / float(self.count_games())
        except:
            return 0.5

    def win_loss_ratio_percentage(self):
        return self.win_loss_ratio() * 100.0

    def team(self):
        return Team.objects.get(name=self.name)

    def __unicode__(self):
        return u'%s' % self.name

class Team(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)
    players = models.ManyToManyField(Player)
    is_team = models.BooleanField()

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
        return self.home_team.filter(result__isnull=False).count() + self.away_team.filter(result__isnull=False).count()

    def count_wins(self):
        return self.home_team.filter(result='1').count() + self.away_team.filter(result='2').count()

    def count_draws(self):
        return self.home_team.filter(result='X').count() + self.away_team.filter(result='X').count()

    def count_losses(self):
        return self.home_team.filter(result='2').count() + self.away_team.filter(result='1').count()

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

    def list_games(self):
        games = Game.objects.filter(result__isnull=False).filter(Q(home_team=self) | Q(away_team=self)).order_by('-date')
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

    def __unicode__(self):
        return u'%s' % self.name

    def clean(self, *args, **kwargs):
        super(Tournament, self).save(*args, **kwargs)
        players = sorted(self.players.all(), key=lambda p: p.team().get_latest_points(), reverse=True)
        teams = []
        if self.is_team:
            while players:
                teams.append(Team.objects.filter(players__in=[players.pop(0)]).get(players__in=[players.pop()]))
        else:
            while players:
                teams.append(Team.objects.get(players__in=[players.pop()], is_team=False))
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


class Game(models.Model):
    home_team = models.ForeignKey(Team, related_name="home_team")
    away_team = models.ForeignKey(Team, related_name="away_team")
    home_fifa_team = models.ForeignKey(FifaTeam, related_name="home_fifa_team", blank=True, null=True)
    away_fifa_team = models.ForeignKey(FifaTeam, related_name="away_fifa_team", blank=True, null=True)
    date = models.DateTimeField("Date of game", auto_now_add=True)
    result = models.CharField("Result", max_length=1, choices=RESULT_CHOICES, blank=True, null=True)
    home_score = models.IntegerField(blank=True, null=True)
    away_score = models.IntegerField(blank=True, null=True)
    date_played = models.DateTimeField("Playtime of game", auto_now=True, blank=True, null=True)
    tournament = models.ForeignKey(Tournament, blank=True, null=True)
    calculate_points = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s: %s - %s' % (self.date, self.home_team, self.away_team)

    def display_score(self):
        if self.result:
            return u'%s - %s' % (self.home_score, self.away_score)
        else:
            return u'Leikur ekki hafinn'

    def winner(self):
        if self.result == "1":
            return self.home_team
        elif self.result == "2":
            return self.away_team
        return None

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
                if changed:
                    if new_points > achievement.points:
                        achievement.game.clear()
                        achievement.points = new_points
                    achievement.game.add(self)
                    achievement.save()

    def save(self, *args, **kwargs):
        if self.calculate_points and Points.objects.filter(game=self).count() == 0:
            if self.result == '1':
                result = 1
            elif self.result == 'X':
                result = 0.5
            else:
                result = 0
            p1 = self.home_team.get_latest_points()
            p2 = self.away_team.get_latest_points()
            e1 = 1/(1+10**((p2-p1)/400))
            e2 = 1/(1+10**((p1-p2)/400))
            p1new = p1+32*(result-e1)
            p2new = p2+32*(1-result-e2)
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
        return teams

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

    def __unicode__(self):
        return u'%s - %s' % (self.game, self.status.name)

class AchievementTemplate(models.Model):
    name = models.CharField("Achievement name", max_length=255, blank=True, null=True)
    icon = models.ImageField(upload_to="achievements")
    predicate = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % (self.name)

class Achievement(models.Model):
    team = models.ForeignKey(Team, blank=True, null=True)
    game = models.ManyToManyField(Game, blank=True, null=True)
    points = models.FloatField(blank=True, null=True)
    template = models.ForeignKey(AchievementTemplate, blank=True, null=True)

    def is_highest(self):
        achievements = Achievement.objects.filter(template=self.template)
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


