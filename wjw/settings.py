import environ
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)

# Read the .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# Zadejte plnou adresu včetně schématu, např. "https://spolekzws.ddns.net".
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Application definition

INSTALLED_APPS_DEFAULT = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
]

INSTALLED_APPS_ALLAUTH = [
    'django.contrib.sites',
    'django.contrib.humanize',

    # Allauth core aplikace
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Poskytovatelé (Providers) pro Google
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.openid_connect',  # MojeID (viz SOCIALACCOUNT_PROVIDERS)
    'seznam_provider',  # vlastní OAuth2 provider pro Seznam.cz
]

INSTALLED_APPS_DEV = ['django_extensions',] if DEBUG else []

# Musí být až po 'django.contrib.admin' (INSTALLED_APPS_DEFAULT), protože
# hijack.contrib.admin při startu dodatečně obaluje už zaregistrovaný UserAdmin.
INSTALLED_APPS_HIJACK = ['hijack', 'hijack.contrib.admin']


INSTALLED_APPS_WAGTAIL = [
    'doc',

    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',

    'modelcluster',
    'taggit',
]

INSTALLED_APPS_MY = [
    'jazzmin',  # musi byt prvni
    'main',
    'django_bootstrap5',
    'phonenumber_field',
    'import_export',
    'simple_history',
]

INSTALLED_APPS = (
    INSTALLED_APPS_MY + INSTALLED_APPS_WAGTAIL + INSTALLED_APPS_DEFAULT + INSTALLED_APPS_HIJACK
    + INSTALLED_APPS_ALLAUTH + INSTALLED_APPS_DEV
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'hijack.middleware.HijackUserMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'allauth.account.middleware.AccountMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',

    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
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
                'main.context_processors.pending_requests_count',
                'main.context_processors.available_classes',
                'main.context_processors.available_circles',
                'main.context_processors.nastenka_pages',
                'main.context_processors.user_avatar_url',
            ],
        },
    },
]

WSGI_APPLICATION = 'wjw.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': env.db(),
    # 'default': {
    #     'ENGINE': 'django.db.backends.sqlite3',
    #     'NAME': BASE_DIR / 'db.sqlite3',
    # }
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
USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = Path(BASE_DIR) / env.str('STATIC_ROOT', default="staticfiles")
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


AUTH_USER_MODEL = 'auth.User'

# Allauth konfigurace
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_LOGIN_METHODS = ['email', ]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # pro začátek 'optional', na produkci 'mandatory'
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
LOGIN_REDIRECT_URL = '/'                 # Kam uživatele přesměrovat po přihlášení
LOGOUT_REDIRECT_URL = '/'

# Nepřihlášeného uživatele na /cms/ přesměrovat na běžné (allauth) přihlášení
# místo defaultního wagtailadmin loginu.
WAGTAILADMIN_LOGIN_URL = '/accounts/login/'

SOCIALACCOUNT_ADAPTER = 'allauth.socialaccount.adapter.DefaultSocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = True

# Pokud přihlášení přes nového poskytovatele přinese ověřený e-mail, který už
# patří existujícímu účtu, rovnou uživatele přihlásíme k tomuto účtu místo
# obecného (a zde slepého, protože ACCOUNT_UNIQUE_EMAIL) formuláře allauth
# pro dokončení registrace. Nový SocialAccount se ale automaticky nepřipojuje
# (AUTO_CONNECT necháváme na výchozí False) - propojení účtů i nadále schvaluje
# správce přes žádosti o sloučení účtů.
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True

SOCIALACCOUNT_PROVIDERS: dict[str, dict[str, object]] = {
    'google': {
        'APPS': [
            {
                'client_id': env.str('GOOGLE_OAUTH_CLIENT_ID', default=''),
                'secret': env.str('GOOGLE_OAUTH_CLIENT_SECRET', default=''),
                'key': ''  # Usually left empty for Google
            },
        ],
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'seznam': {
        'APPS': [
            {
                'client_id': env.str('SEZNAM_OAUTH_CLIENT_ID', default=''),
                'secret': env.str('SEZNAM_OAUTH_CLIENT_SECRET', default=''),
                'key': ''
            },
        ],
    },
    'openid_connect': {
        'APPS': [
            {
                'provider_id': 'mojeid',
                'name': 'MojeID',
                'client_id': env.str('MOJEID_OAUTH_CLIENT_ID', default=''),
                'secret': env.str('MOJEID_OAUTH_CLIENT_SECRET', default=''),
                'settings': {
                    # doplní si '/.well-known/openid-configuration'
                    'server_url': 'https://mojeid.cz',
                },
            },
        ],
    },
}

BOOTSTRAP5 = {
    "alert_dismissible": True,
}

PHONENUMBER_DEFAULT_REGION = "CZ"

MAPY_CZ_API_URL = "https://api.mapy.cz/v1/geocode"
MAPY_CZ_API_KEY = env.str('MAPY_CZ_API_KEY', default='')

# Wagtail
WAGTAIL_SITE_NAME = "Spolek waldorfské školy v Jinonicích"
WAGTAILADMIN_BASE_URL = env.str('WAGTAILADMIN_BASE_URL', default='http://localhost:8000')
WAGTAIL_I18N_ENABLED = False

# https://github.com/wagtail/wagtail/issues/14487 - lze smazat po upgradu wagtailu.
SILENCED_SYSTEM_CHECKS = ["treebeard.E001"]

# django-hijack - přihlášení jako jiný uživatel z Django adminu (viz main.admin.ProfileAdmin).
# Výchozí hodnota, ale uvedena explicitně - přihlásit se jako někdo jiný smí jen superuživatel.
HIJACK_PERMISSION_CHECK = "hijack.permissions.superusers_only"
