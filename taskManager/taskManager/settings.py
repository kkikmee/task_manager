"""
Django settings for taskManager project.
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

# Загружаем .env файл (только локально, на сервере переменные задаются через окружение)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==============================================================
# БЕЗОПАСНОСТЬ
# ==============================================================

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY не задан! Добавьте его в .env или переменные окружения.")

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Парсим ALLOWED_HOSTS из переменной окружения
_allowed_hosts = os.environ.get('ALLOWED_HOSTS', '')
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts.split(',') if h.strip()]

# В режиме разработки добавляем стандартные локальные хосты
if DEBUG:
    ALLOWED_HOSTS += ['localhost', '127.0.0.1', '[::1]']

# Убираем дубликаты
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS))

# ==============================================================
# CSRF
# ==============================================================

CSRF_TRUSTED_ORIGINS = []

# Railway / любой HTTPS-хост
for host in ALLOWED_HOSTS:
    if host not in ('localhost', '127.0.0.1', '[::1]'):
        CSRF_TRUSTED_ORIGINS.append(f'https://{host}')

# ==============================================================
# ПРИЛОЖЕНИЯ
# ==============================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main',
    'users',
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

ROOT_URLCONF = 'taskManager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'taskManager.wsgi.application'

# ==============================================================
# БАЗА ДАННЫХ
# ==============================================================

DATABASE_URL = os.environ.get('DATABASE_URL', '')

if DATABASE_URL:
    # PostgreSQL на Railway или своём сервере
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # SQLite для локальной разработки
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ==============================================================
# ВАЛИДАЦИЯ ПАРОЛЕЙ
# ==============================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==============================================================
# ЛОКАЛИЗАЦИЯ
# ==============================================================

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# ==============================================================
# СТАТИЧЕСКИЕ ФАЙЛЫ
# ==============================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise — сжатие и кэширование статики
if DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ==============================================================
# МЕДИАФАЙЛЫ
# ==============================================================

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================
# ПРОЧЕЕ
# ==============================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.User'

LOGIN_URL = 'user/login/'
LOGIN_REDIRECT_URL = '/'

# ==============================================================
# БЕЗОПАСНОСТЬ В ПРОДАКШЕНЕ (автоматически включается при DEBUG=False)
# ==============================================================

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True