"""
SignSimple UK - Django Settings
PDF document signing & daily sales platform.
Operated by Avyangah Technologies Limited (Company #08235853)
"""
import os
from pathlib import Path
from datetime import timedelta
import environ

env = environ.Env(DEBUG=(bool, False))
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='change-me-in-production')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework', 'rest_framework_simplejwt', 'rest_framework_simplejwt.token_blacklist',
    'corsheaders', 'storages',
    'allauth', 'allauth.account', 'allauth.socialaccount',
    'allauth.socialaccount.providers.google', 'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.microsoft', 'allauth.socialaccount.providers.linkedin_oauth2',
    'authentication', 'documents', 'subscriptions', 'payments', 'organisations', 'sales', 'ai_detector', 'plagiarism', 'chatbot',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', 'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'organisations.middleware.TenantMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [os.path.join(BASE_DIR, 'templates')], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'core.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': env('DB_NAME', default='docsign_uk'), 'USER': env('DB_USER', default='postgres'), 'PASSWORD': env('DB_PASSWORD', default='postgres'), 'HOST': env('DB_HOST', default='localhost'), 'PORT': env('DB_PORT', default='5432')}}
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]

LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'authentication.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1), 'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True, 'BLACKLIST_AFTER_ROTATION': True, 'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256', 'SIGNING_KEY': SECRET_KEY, 'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000', 'http://127.0.0.1:3000'])
CORS_ALLOW_CREDENTIALS = True

USE_S3 = env.bool('USE_S3', default=False)
if USE_S3:
    AWS_ACCESS_KEY_ID = env('S3_ACCESS_KEY', default='')
    AWS_SECRET_ACCESS_KEY = env('S3_SECRET_KEY', default='')
    AWS_STORAGE_BUCKET_NAME = env('S3_BUCKET_NAME', default='docsign-uk')
    AWS_S3_REGION_NAME = env('S3_REGION', default='ewr1')
    AWS_S3_ENDPOINT_URL = env('S3_ENDPOINT_URL', default='')
    AWS_S3_USE_SSL = env.bool('S3_USE_SSL', default=True)
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    if AWS_S3_ENDPOINT_URL:
        AWS_S3_CUSTOM_DOMAIN = None
        AWS_S3_ADDRESSING_STYLE = 'path'
    else:
        AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    AWS_S3_ENCRYPTION = True
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_OBJECT_PARAMETERS = {'ServerSideEncryption': 'AES256'}
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

SITE_ID = 1
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend']
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_UNIQUE_EMAIL = True
OAUTH_FRONTEND_CALLBACK_URL = env('OAUTH_FRONTEND_CALLBACK_URL', default='http://localhost:3000/oauth/callback')

SOCIALACCOUNT_PROVIDERS = {
    'google': {'SCOPE': ['profile', 'email'], 'AUTH_PARAMS': {'access_type': 'online', 'prompt': 'select_account'}, 'APP': {'client_id': env('GOOGLE_CLIENT_ID', default=''), 'secret': env('GOOGLE_CLIENT_SECRET', default=''), 'key': ''}},
    'github': {'SCOPE': ['user:email'], 'APP': {'client_id': env('GITHUB_CLIENT_ID', default=''), 'secret': env('GITHUB_CLIENT_SECRET', default=''), 'key': ''}},
    'microsoft': {'SCOPE': ['openid', 'email', 'profile'], 'APP': {'client_id': env('MICROSOFT_CLIENT_ID', default=''), 'secret': env('MICROSOFT_CLIENT_SECRET', default=''), 'key': ''}},
    'linkedin_oauth2': {'SCOPE': ['openid', 'profile', 'email'], 'APP': {'client_id': env('LINKEDIN_CLIENT_ID', default=''), 'secret': env('LINKEDIN_CLIENT_SECRET', default=''), 'key': ''}},
}
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True

EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@avyangah.co.uk')

CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/1')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://redis:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# ===========================================
# Subscription Plans — Bundled: PDF signing + AI detector
# ===========================================
SUBSCRIPTION_PLANS = {
    'FREE': {
        'name': 'Free',
        'documents_per_month': 10,
        'ai_scans_per_month': 3,
        'price_gbp': 0,
        'description': '10 documents + 3 AI scans every month.',
    },
    'STARTER': {
        'name': 'Starter',
        'documents_per_month': 100,
        'ai_scans_per_month': 100,
        'price_gbp': 2.50,
        'description': '100 documents + 100 AI scans per month.',
    },
    'PROFESSIONAL': {
        'name': 'Professional',
        'documents_per_month': 1000,
        'ai_scans_per_month': 500,
        'price_gbp': 10.00,
        'description': '1,000 documents + 500 AI scans per month.',
    },
}

# Pay-as-you-go extras
EXTRA_DOCS_PRICE_GBP = 1.00
EXTRA_DOCS_BUNDLE_SIZE = 100
EXTRA_AI_SCANS_PRICE_GBP = 2.50
EXTRA_AI_SCANS_BUNDLE_SIZE = 100

TRUELAYER_CLIENT_ID = env('TRUELAYER_CLIENT_ID', default='')
TRUELAYER_CLIENT_SECRET = env('TRUELAYER_CLIENT_SECRET', default='')
TRUELAYER_WEBHOOK_SECRET = env('TRUELAYER_WEBHOOK_SECRET', default='')
TRUELAYER_MERCHANT_ACCOUNT_ID = env('TRUELAYER_MERCHANT_ACCOUNT_ID', default='')
TRUELAYER_SANDBOX = env.bool('TRUELAYER_SANDBOX', default=True)
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_PRICE_STARTER = env('STRIPE_PRICE_STARTER', default='')
STRIPE_PRICE_PROFESSIONAL = env('STRIPE_PRICE_PROFESSIONAL', default='')
STRIPE_PRICE_EXTRA_DOCS = env('STRIPE_PRICE_EXTRA_DOCS', default='')

# ===========================================
# AI Detector — Provider Settings
# ===========================================
HF_API_TOKEN = env('HF_API_TOKEN', default='')
HF_AI_DETECTOR_URL = 'https://api-inference.huggingface.co/models/Hello-SimpleAI/chatgpt-detector-roberta'

# Default provider: 'groq' | 'huggingface' | 'grok' | 'openai'
DEFAULT_AI_DETECTOR_PROVIDER = env('DEFAULT_AI_DETECTOR_PROVIDER', default='groq')

# Groq — FREE, 14,400 req/day — https://console.groq.com
# Shared key: used by AI detector (8b model) AND chatbot (70b model)
GROQ_API_KEY = env('GROQ_API_KEY', default='')
# Quick scan: 8B (131K tokens/min, instant). Deep scan uses 70B hardcoded in services.py
GROQ_MODEL = env('GROQ_MODEL', default='llama-3.1-8b-instant')
GROQ_CHATBOT_MODEL = env('GROQ_CHATBOT_MODEL', default='llama-3.1-8b-instant')
GROK_API_URL = 'https://api.x.ai/v1/chat/completions'
GROK_MODEL = env('GROK_MODEL', default='grok-3-mini')

# OpenAI (optional alternative). Also used to point at a local OpenAI-compatible
# server: set OPENAI_BASE_URL=http://careai-ollama:11434/v1, OPENAI_API_KEY=ollama,
# OPENAI_MODEL=<local model, e.g. llama3.1>.
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_MODEL = env('OPENAI_MODEL', default='gpt-4o-mini')
OPENAI_BASE_URL = env('OPENAI_BASE_URL', default='https://api.openai.com/v1')
OPENAI_TIMEOUT = env.int('OPENAI_TIMEOUT', default=300)

# Google Gemini — FREE, 1000 req/day, 1M context window (no chunking needed)
# Get key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = env('GEMINI_API_KEY', default='')
GEMINI_MODEL = env('GEMINI_MODEL', default='gemini-2.5-flash-lite')

# SiliconFlow — FREE tier, OpenAI-compatible, Llama 3.3/DeepSeek/Qwen
# Sign up at: https://siliconflow.cn
SILICONFLOW_API_KEY = env('SILICONFLOW_API_KEY', default='')
SILICONFLOW_MODEL = env('SILICONFLOW_MODEL', default='meta-llama/Llama-3.3-70B-Instruct')

# Cloudflare Workers AI — FREE 10K neurons/day, Llama 3.1 8B
# Sign up at: https://dash.cloudflare.com → Workers & Pages → AI
CLOUDFLARE_ACCOUNT_ID = env('CLOUDFLARE_ACCOUNT_ID', default='')
CLOUDFLARE_API_TOKEN = env('CLOUDFLARE_API_TOKEN', default='')
CLOUDFLARE_MODEL = env('CLOUDFLARE_MODEL', default='@cf/meta/llama-3.1-8b-instruct')

# Mistral AI — FREE Experiment tier, European/GDPR-friendly, ~1 req/sec
# Get key at: https://console.mistral.ai
MISTRAL_API_KEY = env('MISTRAL_API_KEY', default='')
MISTRAL_MODEL = env('MISTRAL_MODEL', default='mistral-small-latest')

# ===========================================
# Plagiarism Checker — Provider Settings
# ===========================================
# Default: 'groq' (free, pattern analysis) | 'copyleaks' (paid, real web search)
DEFAULT_PLAGIARISM_PROVIDER = env('DEFAULT_PLAGIARISM_PROVIDER', default='groq')

# Copyleaks — real web + academic database search (optional, paid)
# Sign up at https://copyleaks.com/api
COPYLEAKS_API_KEY = env('COPYLEAKS_API_KEY', default='')
COPYLEAKS_EMAIL = env('COPYLEAKS_EMAIL', default='')

# ===========================================
# Security Settings (Reverse Proxy Compatible)
# ===========================================
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_SSL_REDIRECT = False

SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=not DEBUG)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=not DEBUG)

SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000 if not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=not DEBUG)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=not DEBUG)

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[
    'https://signsimple.co.uk',
    'https://www.signsimple.co.uk',
    'http://localhost:3001',
    'http://127.0.0.1:3001',
])

SECURE_REFERRER_POLICY = 'same-origin'

MAX_DOCUMENT_SIZE = 20 * 1024 * 1024
ALLOWED_DOCUMENT_TYPES = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
DOCUMENT_EXPIRY_DAYS = 90

CONVERTIBLE_TO_PDF = {
    'office': ['doc', 'docx'],
    'image': ['jpg', 'jpeg', 'png'],
}
