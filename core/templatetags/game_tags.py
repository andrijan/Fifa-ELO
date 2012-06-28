from django import template

register = template.Library()

@register.filter
def find_game(points, team):
    try:
        return round(points.get(team=team).get_change(),2)
    except:
        return None

