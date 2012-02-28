from django.db import models

MAX = 32
INITIAL_POINTS = 1500.0

class Team(models.Model):
    name = models.CharField("Team name", max_length=255, blank=True, null=True)

    def get_latest_points(self):
        try:
            return Points.objects.filter(team=self).latest('date').points
        except:
            p = Points(team=self, points=1500.0)
            p.save()
            return p.points

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

    def __unicode__(self):
        return u'%s: %s - %s' % (self.date, self.home_team, self.away_team)

    def save(self, *args, **kwargs):
        super(Game, self).save(*args, **kwargs)
        if self.result == '1':
            result = 1
        elif self.result == 'X':
            result = 0.5
        else:
            result = 0
        p1 = self.home_team.get_latest_points()#Points.objects.filter(team=self.home_team).latest('date').points
        p2 = self.away_team.get_latest_points()#Points.objects.filter(team=self.away_team).latest('date').points
        e1 = 1/(1+10**((p2-p1)/400))
        e2 = 1/(1+10**((p1-p2)/400))
        p1new = p1+32*(result-e1)
        p2new = p2+32*(1-result-e2)
        np1 = Points(team=self.home_team,points=p1new)
        np1.save()
        np2 = Points(team=self.away_team,points=p2new)
        np2.save()

class Points(models.Model):
    team = models.ForeignKey(Team)
    date = models.DateTimeField(auto_now_add=True)
    points = models.FloatField("Elo Points")

    def __unicode__(self):
        return u'%s: %s - %s' % (self.date, self.team, self.points)

