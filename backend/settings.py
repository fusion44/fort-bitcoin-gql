"""
Django settings for backend project.

Generated by 'django-admin startproject' using Django 2.0.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import configparser
import datetime
import os

from django.utils.log import DEFAULT_LOGGING

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR + "/logfile.log",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'simple',
        },
        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
    },
    'loggers': {
        '': {
            'level': 'WARNING',
            'handlers': ['console', 'logfile'],
        },
        'backend': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = CONFIG["DEFAULT"]["secret_key"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# CORS_ORIGIN_ALLOW_ALL = True
ALLOWED_HOSTS = ['30a179ba.ngrok.io']

# Application definition

INSTALLED_APPS = [
    'django_celery_beat',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "channels",
    'rest_framework',
    'corsheaders',
    'backend.btc',
    'backend.lnd',
    'backend.stats',
    'backend.user_profile',
    "backend.subscriptions",
    'graphene_django',
]

GRAPHENE = {"MIDDLEWARE": [], 'SCHEMA': 'backend.schema.schema'}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES':
    ('rest_framework.permissions.IsAuthenticated', ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),
}

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA':
    datetime.timedelta(days=1),
    'JWT_REFRESH_EXPIRATION_DELTA':
    datetime.timedelta(days=7),
    'JWT_RESPONSE_PAYLOAD_HANDLER':
    'backend.user_profile.handlers.jwt_response_payload_handler',
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'backend.middleware.JWTMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
ASGI_APPLICATION = "backend.subscriptions.routing.session_application"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache"
    }
}
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

if CONFIG["DEFAULT"]["database"] == "sqlite":
    db = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
elif CONFIG["DEFAULT"]["database"] == "postgres":
    db = {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": CONFIG["POSTGRES"]["postgres.name"],
        "USER": CONFIG["POSTGRES"]["postgres.user"],
        "PASSWORD": CONFIG["POSTGRES"]["postgres.password"],
        "HOST": CONFIG["POSTGRES"]["postgres.host"],
        "PORT": CONFIG["POSTGRES"]["postgres.port"],
}
else:
    raise EnvironmentError("Database must be either sqlite or postgres")

DATABASES = {'default': db}

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME':
        'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME':
        'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

CELERY_BROKER_URL = CONFIG['DEFAULT']['celery_broker_url']
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_TRACK_STARTED = True
