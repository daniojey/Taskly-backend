from .settings import *
from decouple import config


DEBUG = False

CSRF_TRUSTED_ORIGINS = [
    "https://*.railway.app",
]

ALLOWED_HOSTS = [
    "taskly-backend-production-e362.up.railway.app"
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True  
CSRF_COOKIE_SECURE = True     
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SAMESITE = 'None' 
CSRF_COOKIE_SAMESITE = 'None'   


SECURE_HSTS_SECONDS = 3600  # 1 час
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

CSRF_COOKIE_HTTPONLY = False
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_COOKIE_NAME = 'csrftoken'
SESSION_COOKIE_NAME = 'sessionid'