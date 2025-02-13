from pathlib import Path

import os
from dotenv import load_dotenv

# Tải tệp .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-g7_a@=x$x*#2dxm)u03u-kujtofcm0h0ecc$d0(v)2=#)qidk#'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'renthouseapiv2-production.up.railway.app',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '10.0.2.2'
]

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
    "10.0.2.2",
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'drf_yasg',
    'app.apps.AppConfig',
    'rest_framework',
    'social_django',
    'oauth2_provider',
    'corsheaders',
    'debug_toolbar'
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

CORS_ALLOWED_ORIGINS = [
    "https://renthouseapiv2-production.up.railway.app",
    "http://localhost",
    "http://127.0.0.1",
    "http://10.0.2.2",
]

CSRF_TRUSTED_ORIGINS = [
    "https://renthouseapiv2-production.up.railway.app",
]

CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'RentHouseApi.urls'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

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
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'RentHouseApi.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'railway'),
        'USER': os.getenv('MYSQL_USER', 'root'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', 'cqGDHOtSiFHzdyxvXKhsjKGihYHnEotV'),
        'HOST': os.getenv('MYSQL_HOST', 'mysql.railway.internal'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
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

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# custom
import pymysql

pymysql.install_as_MySQLdb()

AUTH_USER_MODEL = 'app.User'

MEDIA_ROOT = '%s/app/static/' % BASE_DIR

# cho phep dang ky token bang json thay vi from data cua post
OAUTH2_PROVIDER = {'OAUTH2_BACKEND_CLASS': 'oauth2_provider.oauth2_backends.JSONOAuthLibCore'}

# Cloudinary Configuration
import cloudinary

cloudinary.config(
    cloud_name="dxcux00kk",
    api_key=os.getenv('CLOUDINAY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_REDIRECT_URI')

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

SOCIAL_AUTH_URL_NAMESPACE = 'social'

SOCIAL_AUTH_USER_MODEL = 'app.User'

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/account/login/callback'

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_by_email',  # Liên kết dựa trên email
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'app.social_auth_pipelines.save_avatar',
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
}

# CLIENT_ID = uxcqnSM8xosdWQZ5OHYGccRy7OsUncKDHvAoUuXD
# CLIENT_SECRET = qUa62PnBlhoCpfeJTzQhqyG1X7iFkIabCB1e2byl5jVpMin843WXEmDbchJMbAdJv3opdviatmaM57Ue3bAWqhbTb9lbnTq75p1Hlp79rojX55PTiC4Nf8VVxUMj9S5h

# email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'bao19042004@gmail.com'
EMAIL_HOST_PASSWORD = 'qdnzlckiyvvrsvfl'
DEFAULT_FROM_EMAIL = 'bao19042004@gmail.com'