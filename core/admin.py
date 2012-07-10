from django.contrib import admin

from models import Achievement, Player, Team, Game, Points, FifaTeam, AchievementTemplate, TournamentGroup, Tournament, TournamentElimination, EliminationStatus

class PlayerAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = self.model.objects_with_deleted.all()
        return qs

class TeamAdmin(admin.ModelAdmin):
    def queryset(self, request):
        qs = self.model.objects_with_deleted.all()
        return qs

class AchievementAdmin(admin.ModelAdmin):
    list_display = ('team', 'template', 'points')

class GameAdmin(admin.ModelAdmin):
    list_display = ('home_team', 'home_fifa_team', 'away_fifa_team', 'away_team', 'result', 'home_score', 'away_score')

admin.site.register(TournamentElimination)
admin.site.register(EliminationStatus)
admin.site.register(Tournament)
admin.site.register(TournamentGroup)
admin.site.register(AchievementTemplate)
admin.site.register(FifaTeam)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Points)
