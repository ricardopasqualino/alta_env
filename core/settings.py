from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('DJANGO_SECRET_KEY', default='default-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['alta-env.onrender.com', 
                 'localhost', 
                 '127.0.0.1', 
                 'alta.bi',
                 'app.alta.bi',
                 ]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'alta',
    'django_filters',
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
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

WSGI_APPLICATION = 'core.wsgi.application'



# Configuração do Banco de Dados usando variáveis de ambiente
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='alta_db_prod_2'),
        'USER': config('DB_USER', default='alta_db_prod_2_user'),
        'PASSWORD': config('DB_PASSWORD', default='3rp700XExUxgrfqCIPgvChVMOwWUyQUB'),
        'HOST': config('DB_HOST', default='dpg-d088hrfdiees7391qrc0-a.oregon-postgres.render.com'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}


# DATABASES = {
#     'default': {
#         'ENGINE': config('DB_ENGINE_2'),
#         'NAME': config('DB_NAME_2'),
#         'USER': config('DB_USER_2'),
#         'PASSWORD': config('DB_PASSWORD_2'),
#         'HOST': config('DB_HOST_2'),
#         'PORT': config('DB_PORT_2'),
#     }
# }





# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# This setting informs Django of the URI path from which your static files will be served to users
# Here, they well be accessible at your-domain.onrender.com/static/... or yourcustomdomain.com/static/...
STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]


# This production code might break development mode, so we check whether we're in DEBUG mode
if not DEBUG:
    # Tell Django to copy static assets into a path called `staticfiles` (this is specific to Render)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Enable the WhiteNoise storage backend, which compresses static files to reduce disk use
    # and renames the files with unique names for each version to support long-term caching
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Expiração da sessão no navegador após 2 horas de inatividade
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 7200  # 2 horas em segundos

# Aumentar o timeout das requisições
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
TIMEOUT = 300  # 5 minutos


# Configurações de Email
# Em desenvolvimento, usa console backend (não envia email real)
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("📧 Modo de desenvolvimento: emails serão exibidos no console")
else:
    # Em produção, usa SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='ricardo.pasqualino@gmail.com')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='ricardo.pasqualino@gmail.com')
    
    print("📧 Modo de produção: usando SMTP Gmail")
    print(f"📧 EMAIL_HOST_USER: {EMAIL_HOST_USER}")
    print(f"📧 EMAIL_HOST_PASSWORD configurada: {'Sim' if EMAIL_HOST_PASSWORD else 'Não'}")
    print(f"📧 DEFAULT_FROM_EMAIL: {DEFAULT_FROM_EMAIL}")
    
    # Verificar se as configurações de email estão corretas
    if not EMAIL_HOST_PASSWORD:
        print("⚠️ ATENÇÃO: EMAIL_HOST_PASSWORD não configurada!")
        print("   Configure a variável de ambiente EMAIL_HOST_PASSWORD no Render")
        print("   Use a senha de app do Gmail (não a senha normal)")
    if not EMAIL_HOST_USER:
        print("⚠️ ATENÇÃO: EMAIL_HOST_USER não configurada!")
        print("   Configure a variável de ambiente EMAIL_HOST_USER no Render")
    else:
        print("✅ Configurações de email carregadas com sucesso")

# Configurações de Webhook
if DEBUG:
    RENDER_EXTERNAL_URL = 'localhost:8000'  # Para desenvolvimento local
else:
    RENDER_EXTERNAL_URL = config('RENDER_EXTERNAL_URL', default='alta-env.onrender.com')
    # Se a URL já contém https://, remover para evitar duplicação
    if RENDER_EXTERNAL_URL.startswith('https://'):
        RENDER_EXTERNAL_URL = RENDER_EXTERNAL_URL.replace('https://', '')
    elif RENDER_EXTERNAL_URL.startswith('http://'):
        RENDER_EXTERNAL_URL = RENDER_EXTERNAL_URL.replace('http://', '')

# Configuração de Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutos
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}
