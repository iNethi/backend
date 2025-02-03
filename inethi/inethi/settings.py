"""
Django settings for inethi project.

Generated by 'django-admin startproject' using Django 5.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""
import json
import os
from pathlib import Path
import environ
from keycloak import KeycloakOpenID, KeycloakOpenIDConnection, KeycloakAdmin
env = environ.Env(
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
)
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
if os.path.exists(os.path.join(BASE_DIR, ".env")):
    environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY=env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG=env("DEBUG")

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'rest_framework',
    'drf_spectacular',
    'corsheaders',
    # iNethi Apps
    'user',
    'wallet',
    'radiusdesk',
    'api_key'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'inethi.urls'
# For admin site authentication


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

WSGI_APPLICATION = 'inethi.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_HOST'),
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Johannesburg'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
AUTH_USER_MODEL = 'core.User'

# Keycloak config
KEYCLOAK_OPENID = KeycloakOpenID(
    server_url=env("KEYCLOAK_URL"),
    client_id=env("KEYCLOAK_BACKEND_CLIENT_ID"),
    realm_name=env("KEYCLOAK_REALM"),
    client_secret_key=env("KEYCLOAK_CLIENT_SECRET"),
)

KEYCLOAK_CONNECTION = KeycloakOpenIDConnection(
    server_url=env("KEYCLOAK_URL"),
    username=env("KEYCLOAK_ADMIN"),
    password=env("KEYCLOAK_ADMIN_PASSWORD"),
    realm_name=env("KEYCLOAK_REALM"),
    user_realm_name=env("KEYCLOAK_REALM"),
    client_id=env("KEYCLOAK_BACKEND_CLIENT_ID"),
    client_secret_key=env("KEYCLOAK_CLIENT_SECRET"),
    verify=True
)

KEYCLOAK_ADMIN = KeycloakAdmin(connection=KEYCLOAK_CONNECTION)

# Krone config
krone_abi_fp = os.path.join(BASE_DIR, "contracts/krone_contract_abi.json")
with open(krone_abi_fp, "r", encoding="utf-8") as abi_file:
    ABI_FILE_PATH = krone_abi_fp
    KRONE_CONTRACT_ABI = json.load(abi_file)
WALLET_ENCRYPTION_KEY = env("WALLET_ENCRYPTION_KEY")
BLOCKCHAIN_PROVIDER_URL = env("BLOCKCHAIN_PROVIDER_URL")
CONTRACT_ADDRESS=env("CONTRACT_ADDRESS")

SPECTACULAR_SETTINGS = {
    'TITLE': 'iNethi API',
    'DESCRIPTION': 'iNethi Backend API',
    'VERSION': '0.0.1',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# Smart contracts
FAUCET_ABI_FILE_PATH = os.path.join(BASE_DIR, "contracts/faucet_abi.json")
REGISTRY_ABI_FILE_PATH = os.path.join(BASE_DIR, "contracts/registry_abi.json")
REGISTRY_ADDRESS = env("REGISTRY_ADDRESS")
FAUCET_ADDRESS =env("FAUCET_ADDRESS")

# owner of smart contracts
ACCOUNT_INDEX_ADMIN_WALLET_ADDRESS=env("ACCOUNT_INDEX_ADMIN_WALLET_ADDRESS")
FAUCET_ADMIN_WALLET_ADDRESS=env("FAUCET_ADMIN_WALLET_ADDRESS")

# Enable account index and faucet
FAUCET_AND_INDEX_ENABLED=env("FAUCET_AND_INDEX_ENABLED")