from django.contrib import admin

from models import Achievement, Player, Team, Game, Points

class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'points')

admin.site.register(Achievement, AchievementAdmin)
admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Game)
admin.site.register(Points)
