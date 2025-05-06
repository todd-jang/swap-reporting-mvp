# my_django_project/settings.py

# ... (기존 Django 설정 코드) ...

# 인증 관련 설정
# ID 토큰을 발급하는 Identity Provider의 JWKS 엔드포인트 URL
AUTH_JWKS_URL = "YOUR_IDENTITY_PROVIDER_JWKS_URL" # 실제 URL로 변경

# 여러분의 애플리케이션 Audience (IdP 설정에 따름)
AUTH_AUDIENCE = "YOUR_AUDIENCE" # 실제 값으로 변경

# 토큰 발급자 (IdP의 iss 클레임 값)
AUTH_ISSUER = "YOUR_ISSUER" # 실제 값으로 변경

# 관리자 권한을 나타내는 커스텀 클레임 이름
AUTH_ADMIN_CLAIM_NAME = "admin" # 실제 클레임 이름으로 변경

# 토큰 서명 알고리즘 (IdP에 따라 다름, 예: RS256)
AUTH_TOKEN_ALGORITHMS = ["RS256"]

# ... (나머지 설정 코드) ...
