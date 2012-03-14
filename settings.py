# -*- coding: utf-8 -*-

import posixpath

from path import path
import os

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'x4$@%buj5c@g6@m(fzhtsv+2z9z88(a0a6_p__yjd)nimv#a)l'

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SERVE_MEDIA = DEBUG

PROJECT_ROOT = path(__file__).abspath().realpath().dirname()
ROOT_PATH = os.path.normpath(os.path.dirname(__file__))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'dev.db',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Vienna'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

ugettext = lambda s: s # rather hackish but suggested by...
## ... http://docs.djangoproject.com/en/1.1/topics/i18n/deployment/#how-django-discovers-language-preference
## to prevent circular dependancies
LANGUAGES = (
    ('en', ugettext('English')),
    #('de', ugettext('German')),
)

DEFAULT_HTTP_PROTOCOL = 'http'

SITE_ID = 1

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = PROJECT_ROOT / 'assets' / 'uploaded' / '' # ensure trailing slash

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = ROOT_PATH + "/static" + '/' # ensure trailing slash

# Additional directories which hold static files
STATICFILES_DIRS = [
    ROOT_PATH + "/assets/static",
]

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/assets/uploaded'

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/assets/static/"

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")

# autoload this templatetags in every template
TEMPLATE_TAGS = ( "django.templatetags.i18n",
                  "easy_thumbnails.templatetags.thumbnail",
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    PROJECT_ROOT / "templates",
)

CONTEXT_SETTINGS = (
    "DEBUG", "MEDIA_URL", "STATIC_URL",
)

CONTEXT_REQUEST_VARS = (
)

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    'django.core.context_processors.static',
    "django.contrib.messages.context_processors.messages",

    'core.context_processors.global_settings',
    'core.context_processors.request_params',
    'core.context_processors.site_url',
]
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.markup',
    'django.contrib.messages',

    #external
    'django_extensions',
    'easy_thumbnails',
    'googlecharts',

    #Database
    'django_evolution',

    #internal
    'core',
)

# Subject-line prefix for e-mail messages sent with django.core.mail.mail_admins or django.core.mail.mail_managers. You'll probably want to include the trailing space.
EMAIL_SUBJECT_PREFIX = u'[Django-Project] '

# The host to use for sending e-mail.
EMAIL_HOST = u'localhost'

# Password to use for the SMTP server defined in EMAIL_HOST. This setting is used in conjunction with EMAIL_HOST_USER when authenticating to the SMTP server. If either of these settings is empty, Django won't attempt authentication.
EMAIL_HOST_PASSWORD = ''
# Username to use for the SMTP server defined in EMAIL_HOST. If empty, Django won't attempt authentication.
EMAIL_HOST_USER = ''

# Port to use for the SMTP server defined in EMAIL_HOST.
EMAIL_PORT = 25
# Whether to use a TLS (secure) connection when talking to the SMTP server.
EMAIL_USE_TLS = False


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
try:
    from local_settings import *
except ImportError:
    pass
