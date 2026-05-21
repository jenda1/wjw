from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-m)t#l9i7x#fn6w!0g_j33=zugy&)jr3gafy2x9d*5k7a^!mxo!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [ ]


# Application definition

INSTALLED_APPS_DEFAULT = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

INSTALLED_APPS_ALLAUTH = [
    'django.contrib.sites',
    'django.contrib.humanize',

    # Allauth core aplikace
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Poskytovatelé (Providers) pro Google a Facebook
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
]

INSTALLED_APPS_DEV = ['django_extensions',] if DEBUG else []


INSTALLED_APPS_MY = [
    # Tvoje vlastní aplikace
    'main',
    'django_bootstrap5',
    'phonenumber_field',
]

INSTALLED_APPS = INSTALLED_APPS_DEFAULT + INSTALLED_APPS_ALLAUTH + INSTALLED_APPS_DEV + INSTALLED_APPS_MY

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'wjw.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'wjw.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

SITE_ID = 1

LANGUAGE_CODE = 'cs'

TIME_ZONE = 'Europe/Prague'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"


# Allauth konfigurace
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Konfigurace chování Allauth (volitelné, ale doporučené)
ACCOUNT_LOGIN_METHODS = ['email', ]
#ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # pro začátek 'optional', na produkci 'mandatory'
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
LOGIN_REDIRECT_URL = '/'                 # Kam uživatele přesměrovat po přihlášení
LOGOUT_REDIRECT_URL = '/'
