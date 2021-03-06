"""
Django settings for bugbounty project.

Generated by 'django-admin startproject' using Django 1.11.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
from dotenv import load_dotenv
import dj_database_url
import dj_email_url

from dashboard.h1 import ProgramConfiguration
from .settings_utils import (load_cups_from_vcap_services, is_on_cloudfoundry,
                             load_database_url_from_vcap_services)


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

dotenv_path = os.path.join(BASE_DIR, '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

if is_on_cloudfoundry():
    load_cups_from_vcap_services(name='bbdash-env')
    load_database_url_from_vcap_services(name='bbdash-env', service='aws-rds')
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

H1_PROGRAMS = ProgramConfiguration.parse_list_from_environ(
    prefix='H1_PROGRAM_',
    environ=os.environ,
)

SLA_METRICS_CONTRACT_START_DAY = 7

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = 'DEBUG' in os.environ

if DEBUG:
    os.environ.setdefault(
        'SECRET_KEY',
        'This is a fake secret key for development/debugging only'
    )
    os.environ.setdefault(
        'EMAIL_URL',
        os.environ.get('DEFAULT_DEBUG_EMAIL_URL', 'console:')
    )
    os.environ.setdefault('DEFAULT_FROM_EMAIL', 'noreply@localhost')
else:
    # Assume HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

CSRF_COOKIE_HTTPONLY = True

email_config = dj_email_url.parse(os.environ['EMAIL_URL'])
# Sets a number of settings values, as described at
# https://github.com/migonzalvar/dj-email-url
vars().update(email_config)

DEFAULT_FROM_EMAIL = os.environ['DEFAULT_FROM_EMAIL']

SECRET_KEY = os.environ['SECRET_KEY']

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.postgres',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'uaa_client',
    'dashboard.apps.DashboardConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'bugbounty.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'environment': 'bugbounty.jinja2.environment',
        },
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
            ]
        }
    },
]

WSGI_APPLICATION = 'bugbounty.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.parse(os.environ['DATABASE_URL'])
}


AUTHENTICATION_BACKENDS = [
    'uaa_client.authentication.UaaBackend',
]

UAA_APPROVED_DOMAINS = [
    'gsa.gov',
]

UAA_AUTH_URL = 'https://login.fr.cloud.gov/oauth/authorize'

UAA_TOKEN_URL = 'https://uaa.fr.cloud.gov/oauth/token'

UAA_CLIENT_ID = os.environ.get('UAA_CLIENT_ID', 'bugbounty-dev')

UAA_CLIENT_SECRET = os.environ.get('UAA_CLIENT_SECRET')

if not UAA_CLIENT_SECRET:
    if DEBUG:
        # We'll be using the Fake UAA Provider.
        UAA_CLIENT_SECRET = 'fake-uaa-provider-client-secret'
        UAA_AUTH_URL = UAA_TOKEN_URL = 'fake:'

LOGIN_URL = 'uaa_client:login'

LOGIN_REDIRECT_URL = '/'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] "
                      "%(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'bugbounty.log'),
            'formatter': 'verbose'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'propagate': True,
            'level': 'INFO',
        },
        'scheduler': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'collected-static')
