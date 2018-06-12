import os
from datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '&b&w8j=$1)rqoa37oybydw_hi%mg-l&m$9c0$m6+y%)*bf6%z1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'crowdsrc.src.apps.CrowdsrcConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'auditlog'
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'crowdsrc.src.authentication.ExpiringTokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'crowdsrc.urls'

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

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

WSGI_APPLICATION = 'crowdsrc.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ATOMIC_REQUESTS': True,
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'crowdsrc',
                'USER': 'root',
                'PASSWORD': 'pass',
                'HOST': 'localhost',
                'PORT': '',
    }
}

# Database audit settings
# https://django-auditlog.readthedocs.io/en/stable/

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Minimum password length
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CORS_ORIGIN_ALLOW_ALL = False
CORS_ORIGIN_WHITELIST = ('localhost:4200')

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'contact.crowdsrc@gmail.com'
EMAIL_HOST_PASSWORD = 'hr5rphDNlHKCL68tMIjH'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

BASE_DOMAIN = 'http://localhost:4200'

STATIC_URL = 'static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
USER_IMAGE_ROOT = os.path.join(MEDIA_ROOT, 'user_images')
TASK_SUBMISSION_ROOT = os.path.join(MEDIA_ROOT, 'submissions')

# Audit actions
CREATE = 0
UPDATE = 1
DELETE = 2

# Captcha settings
GOOGLE_RECAPTCHA_SECRET_KEY = '6LfC-kYUAAAAAJe3MOoAWZ6z8Jl9UAnkHjyKAYYB'

# Time to expire user auth tokens/refresh tokens
TOKEN_EXPIRE_TIME = timedelta(minutes=10)
REFRESH_TOKEN_EXPIRE_TIME = timedelta(days=14)

# Global values for User privacy settings
USER_PERMISSION_ROLES = ['public', 'crowd', 'me']
MIN_USER_PERMISSION = 0
MAX_USER_PERMISSION = len(USER_PERMISSION_ROLES) - 1

# Global values for task status levels
TASK_STATUS_NAMES = ['incomplete', 'pending approval', 'complete']
MIN_TASK_STATUS = 0
MAX_TASK_STATUS = len(TASK_STATUS_NAMES) - 1

# Skill weight settings
# the weight for the submission overall rating
ALPHA = 1 / 3
# the weight for the submission skill rating
BETA = 2 / 3
# the score bonus for accepted submissions
DELTA = 5
