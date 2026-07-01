"""
Django settings for GEO Metadata Engine project.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False; must be explicitly set to "True" in the environment to enable.
DEBUG = os.environ.get("DEBUG", "") == "True"

# Comma-separated list of allowed hosts, e.g. "example.ch,www.example.ch".
# Defaults to localhost for local development.
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# Comma-separated list of trusted origins for CSRF, with scheme,
# e.g. "https://example.ch,https://www.example.ch". Required when serving over
# HTTPS behind an ingress/proxy. Empty by default for local development.
CSRF_TRUSTED_ORIGINS = [
    origin
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin
]

# TLS is terminated at the ingress/router, so requests reach the app over plain
# HTTP internally. Trust the X-Forwarded-Proto header so Django builds absolute
# URLs (e.g. the ADFS OAuth redirect_uri) with the correct https scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Application definition

INSTALLED_APPS = [
    "editor.apps.EditorConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "django_auth_adfs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

ROOT_URLCONF = "metadata.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "metadata.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
        "TIME_ZONE": "Europe/Zurich",
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "de-ch"

TIME_ZONE = "Europe/Zurich"

USE_I18N = True

# Formats dates, numbers etc. according to LANGUAGE_CODE (e.g. 31.03.2026)
USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "django_auth_adfs.backend.AdfsAuthCodeBackend",
]

AUTH_ADFS = {
    "SERVER": os.environ.get("ADFS_SERVER"),
    "CLIENT_ID": os.environ.get("ADFS_CLIENT_ID"),
    "CLIENT_SECRET": os.environ.get("ADFS_CLIENT_SECRET"),
    "RELYING_PARTY_ID": os.environ.get("ADFS_RELYING_PARTY_ID"),
    "AUDIENCE": os.environ.get("ADFS_AUDIENCE"),
    "CA_BUNDLE": True,
    # ADFS token has no 'winaccountname' claim (django-auth-adfs's default);
    # key the Django user on 'email', which the token does provide.
    "USERNAME_CLAIM": "email",
    "CLAIM_MAPPING": {
        "first_name": "given_name",
        "last_name": "family_name",
        "email": "email",
    },
    "GROUP_CLAIM": "group",
    "MIRROR_GROUPS": True,
}

LOGIN_URL = "django_auth_adfs:login"
LOGIN_REDIRECT_URL = "/"

# Temporary DEBUG logging for the ADFS OIDC flow. Prints the token request
# (token endpoint, redirect_uri, and whether client_secret/code_verifier are
# sent) to stdout, which surfaces in the pod logs. Used to diagnose the
# MSIS9612 "authorization code is invalid" error at the token exchange step.
# Remove once ADFS login is working.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django_auth_adfs": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
    },
}
