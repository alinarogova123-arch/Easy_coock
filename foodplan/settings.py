from pathlib import Path

from environs import env

env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env.str(
    'SECRET_KEY',
    'django-insecure-fn)odhs9c(6agcu8&=pdde(w8l3@lka7*g(w7$h@gbnu569vr9',
)

DEBUG = env.bool('DEBUG', True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'recipes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodplan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'foodplan.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


STATIC_URL = env.str('STATIC_URL', '/static/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]


MEDIA_URL = env.str('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / 'media'


BREAKFAST_PRICE = env.int('BREAKFAST_PRICE', 200)
LUNCH_PRICE = env.int('LUNCH_PRICE', 300)
DINNER_PRICE = env.int('DINNER_PRICE', 400)
DESSERT_PRICE = env.int('DESSERT_PRICE', 100)

YOOKASSA_SHOP_ID = env.str('YOOKASSA_SHOP_ID', '')
YOOKASSA_SECRET_KEY = env.str('YOOKASSA_SECRET_KEY', '')
YOOKASSA_RETURN_URL = env.str(
    'YOOKASSA_RETURN_URL',
    'http://127.0.0.1:8000/payment/callback/',
)
