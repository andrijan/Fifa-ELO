#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType

def run():

    from django.contrib.auth.models import User

    auth_user_1 = User(username=u'stephan',
                       first_name=u'Stephan',
                       last_name=u'Pötschner',
                       email=u'stephan.poetschner@gmail.com',
                       is_staff=True,
                       is_superuser=True,
                       is_active=True,
                       last_login=datetime.datetime(2010, 7, 9, 8, 57, 49, 
                                                      727622),
                       date_joined=datetime.datetime(2010, 7, 9, 8, 57, 49, 727622)
                       )
    auth_user_1.set_password(u'localhost')
    auth_user_1.save()