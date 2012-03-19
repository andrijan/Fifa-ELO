from django.contrib import admin

from models import Achievement, Player, Team, Game, Points, FifaTeam

class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'points')

class GameAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'home_fifa_team', 'away_fifa_team', 'away_team', 'result', 'home_score', 'away_score')

admin.site.register(FifaTeam)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Game, GameAdmin)
admin.site.register(Points)
