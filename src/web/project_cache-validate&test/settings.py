# my_django_project/settings.py

from decouple import config, Csv
import dj_database_url # DATABASE_URL 환경 변수를 파싱하기 위해 필요 (pip install dj_database_url)
import os # BASE_DIR 경로 설정을 위해 필요

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# WARNING: keep the secret key used in production secret!
# 환경 변수에서 SECRET_KEY를 읽어옵니다. .env 파일에 정의하거나 서버 환경 변수로 설정해야 합니다.
SECRET_KEY = config('SECRET_KEY')

# WARNING: don't run with debug turned on in production!
# 환경 변수에서 DEBUG 값을 읽어옵니다. 프로덕션 환경에서는 반드시 'off' 또는 False로 설정해야 합니다.
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv()) # NCP 서버의 Public IP 또는 도메인 입력


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app', # 여러분의 앱 등록
    # 'rest_framework', # DRF 사용하는 경우
]

# ... (MIDDLEWARE, ROOT_URLCONF 등 기존 설정) ...

TEMPLATES = [
    # ...
]

WSGI_APPLICATION = 'my_django_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# 환경 변수에서 DATABASE_URL을 읽어와 데이터베이스 설정
DATABASES = {
    'default': config('DATABASE_URL', cast=dj_database_url.parse)
}


# Password validation
# ...

# Internationalization
# ...

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
# collectstatic 명령으로 정적 파일이 모일 디렉터리 (배포 시 중요)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Default primary key field type
# ...

# --- 인증 관련 설정 (token_verification.py에서 사용) ---
# 이 값들은 환경 변수에서 읽어오거나, 코드에 직접 둘 수 있습니다.
# 민감하지 않다면 settings.py에 직접 두는 것도 가능합니다.
AUTH_JWKS_URL = "YOUR_IDENTITY_PROVIDER_JWKS_URL" # 실제 URL로 변경
AUTH_AUDIENCE = "YOUR_AUDIENCE" # 실제 값으로 변경
AUTH_ISSUER = "YOUR_ISSUER" # 실제 값으로 변경
AUTH_ADMIN_CLAIM_NAME = "admin" # 실제 클레임 이름으로 변경
AUTH_TOKEN_ALGORITHMS = ["RS256"] # IdP에 따라 다름

