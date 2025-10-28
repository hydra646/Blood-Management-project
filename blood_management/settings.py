import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'dev-key-change-in-prod'
DEBUG = True
ALLOWED_HOSTS = []
INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework','corsheaders','django_filters','core',
]
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'blood_management.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':[
    'django.template.context_processors.debug','django.template.context_processors.request',
    'django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages',]},},]
WSGI_APPLICATION = 'blood_management.wsgi.application'
DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

# Multi-language support
from django.utils.translation import gettext_lazy as _
LANGUAGES = [
    ('en', _('English')),
    ('bn', _('Bangla')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.User'
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticatedOrReadOnly'],
    # Allow both session-based auth (for the browsable API and frontend session login)
    # and JWT auth (for API clients). SessionAuthentication enforces CSRF for unsafe methods.
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}
from datetime import timedelta
SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),'REFRESH_TOKEN_LIFETIME': timedelta(days=1)}
CORS_ALLOW_ALL_ORIGINS = True
# Email backend for dev (console) by default
# To actually deliver emails (e.g. to Mailtrap or SMTP), set the SMTP_* environment
# variables below. When SMTP_HOST is present, SMTP settings will override the
# console backend.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'amarsopno3504@gmail.com'

# Allow overriding the default "from" address via environment variable so the
# website/owner email can be used as the sender for confirmation emails.
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
# If an EMAIL_FILE_PATH env var is set, use the file-based backend so sent
# messages are written to files for easy inspection during development.
if os.environ.get('EMAIL_FILE_PATH'):
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = Path(os.environ.get('EMAIL_FILE_PATH'))

# Optional SMTP configuration (use environment variables to enable):
# Example Mailtrap (set these env vars in your environment or a .env file):
#   SMTP_HOST=smtp.mailtrap.io
#   SMTP_PORT=2525
#   SMTP_USER=<mailtrap-user>
#   SMTP_PASSWORD=<mailtrap-password>
#   SMTP_USE_TLS=False
# When SMTP_HOST is set, the project will switch to the SMTP backend.
if os.environ.get('SMTP_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('SMTP_HOST')
    EMAIL_PORT = int(os.environ.get('SMTP_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('SMTP_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASSWORD')
    # Allow controlling TLS/SSL via env; default to True for port 587
    EMAIL_USE_TLS = os.environ.get('SMTP_USE_TLS', 'True') == 'True'
    EMAIL_USE_SSL = os.environ.get('SMTP_USE_SSL', 'False') == 'True'
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
# Login redirect settings to match frontend URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
