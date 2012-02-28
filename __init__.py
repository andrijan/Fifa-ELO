# -*- coding: utf-8 -*-

from django.conf import settings
from django.template import add_to_builtins

try:
    for lib in settings.TEMPLATE_TAGS:
        add_to_builtins(lib)
except AttributeError:
    pass

