from django.db import models

MAX = 32
INITIAL_POINTS = 1500.0

class Team(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)
    is_team = models.BooleanField()

    def get_latest_points(self):
        try:
            return Points.objects.filter(team=self).latest('date').points
        except:
            p = Points(team=self, points=1500.0, date='2012-02-27 12:00:00')
            p.save()
            return p.points

    def get_change(self):
        current = self.get_latest_points()
        try:
            old = self.points_set.all().order_by('-date')[1].points
        except:
            return "same"
        if current > old:
            return "up"
        elif current < old:
            return "down"
        else:
            return "same"

    def count_games(self):
        return self.home_team.count() + self.away_team.count()

    def count_wins(self):
        return self.home_team.filter(result='1').count() + self.away_team.filter(result='2').count()

    def count_draws(self):
        return self.home_team.filter(result='X').count() + self.away_team.filter(result='X').count()

    def count_losses(self):
        return self.home_team.filter(result='2').count() + self.away_team.filter(result='1').count()

    def __unicode__(self):
        return u'%s' % self.name

RESULT_CHOICES = (
    ('1', '1'),
    ('X', 'X'),
    ('2', '2'),
)

class Game(models.Model):
    home_team = models.ForeignKey(Team, related_name="home_team")
    away_team = models.ForeignKey(Team, related_name="away_team")
    date = models.DateTimeField("Date of game", auto_now_add=True)
    result = models.CharField("Result", max_length=1, choices=RESULT_CHOICES)
    home_score = models.IntegerField(blank=True, null=True)
    away_score = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return u'%s: %s - %s' % (self.date, self.home_team, self.away_team)

    def save(self, *args, **kwargs):
        if not self.pk:
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
            np1 = Points(team=self.home_team,points=p1new, game=self)
            np1.save()
            np2 = Points(team=self.away_team,points=p2new, game=self)
            np2.save()
        super(Game, self).save(*args, **kwargs)

class Points(models.Model):
    team = models.ForeignKey(Team)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    points = models.FloatField("Elo Points")
    game = models.ForeignKey(Game, null=True, blank=True)

    def __unicode__(self):
        return u'%s: %s - %s' % (self.date, self.team, self.points)

