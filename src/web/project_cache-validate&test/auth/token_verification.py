import jwt
from jwk import PyJWKClient
import requests # PyJWKClient 내부에서 사용될 수 있습니다.
import time

# --- 설정 (실제 값으로 변경 필요) ---
# ID 토큰을 발급하는 Identity Provider의 JWKS 엔드포인트 URL
# 예시: Firebase Auth는 https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com 사용
JWKS_URL = "YOUR_IDENTITY_PROVIDER_JWKS_URL"

# 여러분의 애플리케이션 Audience (IdP 설정에 따름)
# 예시: Firebase Auth 프로젝트 ID
AUDIENCE = "YOUR_AUDIENCE"

# 토큰 발급자 (IdP의 iss 클레임 값)
# 예시: Firebase Auth는 https://securetoken.google.com
ISSUER = "YOUR_ISSUER"

# 관리자 권한을 나타내는 커스텀 클레임 이름
ADMIN_CLAIM_NAME = "admin"

# --- JWK 클라이언트 설정 (애플리케이션 초기화 시 한 번만 실행) ---
# PyJWKClient 인스턴스는 JWKS를 가져오고 캐싱하는 로직을 내부적으로 관리합니다.
# 따라서 애플리케이션이 실행되는 동안 이 클라이언트 인스턴스를 재사용하는 것이 좋습니다.
try:
    # JWKS 엔드포인트로부터 키를 가져오는 클라이언트 생성
    # get_signing_key_from_jwt() 호출 시 필요에 따라 실제 JWKS를 가져옵니다.
    jwk_client = PyJWKClient(JWKS_URL)
    print(f"JWK Client created for URL: {JWKS_URL}")
except Exception as e:
    print(f"Error creating PyJWKClient: {e}")
    # 애플리케이션 시작 시 JWKS 엔드포인트 접근에 문제가 있다면 여기서 예외 처리
    # (네트워크 설정, URL 오류 등)
    # 실제 운영 환경에서는 애플리케이션 시작을 중단하거나 오류 로깅 필요

# --- ID 토큰 검증 및 관리자 권한 확인 함수 ---
def verify_id_token_and_check_admin(id_token: str) -> dict:
    """
    ID 토큰을 검증하고, 유효한 경우 관리자 권한을 확인합니다.

    Args:
        id_token: 클라이언트로부터 받은 ID 토큰 문자열.

    Returns:
        검증된 토큰의 페이로드(클레임) 딕셔너리.
        관리자 권한이 없거나 토큰이 유효하지 않으면 예외 발생.

    Raises:
        ValueError: ID 토큰이 제공되지 않았거나 형식이 잘못된 경우.
        jwt.ExpiredSignatureError: 토큰이 만료된 경우.
        jwt.InvalidAudienceError: 토큰의 Audience가 일치하지 않는 경우.
        jwt.InvalidIssuerError: 토큰의 Issuer가 일치하지 않는 경우.
        jwt.InvalidSignatureError: 토큰 서명이 유효하지 않은 경우.
        jwt.DecodeError: 토큰 디코딩 중 오류 발생.
        Exception: 서명 키를 가져오지 못했거나 기타 처리 중 오류 발생.
        PermissionError: 관리자 권한이 없는 경우 (커스텀 예외).
    """
    if not id_token:
        raise ValueError("ID Token is missing.")

    signing_key = None
    try:
        # 토큰 헤더에서 kid를 추출하여 해당 서명 키를 PyJWKClient로부터 가져옵니다.
        # PyJWKClient는 내부적으로 캐싱 로직을 수행합니다.
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        print(f"Signing key obtained using kid: {signing_key.kid}")

    except Exception as e:
        # 서명 키를 가져오는데 실패한 경우 (네트워크 문제, kid 불일치, JWKS 엔드포인트 오류 등)
        print(f"Error getting signing key: {e}")
        raise Exception("Failed to get signing key for ID token.") from e

    try:
        # PyJWT를 사용하여 토큰의 서명 및 표준 클레임을 검증합니다.
        # audience와 issuer를 지정하면 PyJWT가 자동으로 해당 클레임을 검증합니다.
        payload = jwt.decode(
            id_token,
            signing_key.public_key, # PyJWKClient에서 가져온 공개 키 사용
            algorithms=["RS256"], # 토큰에 사용된 암호화 알고리즘 지정 (IdP에 따라 다름)
            audience=AUDIENCE,
            issuer=ISSUER,
            options={"verify_signature": True, "verify_exp": True, "verify_aud": True, "verify_iss": True}
            # 'verify_exp', 'verify_aud', 'verify_iss' 옵션을 True로 설정하면 PyJWT가 자동으로 검증
            # 'leeway' 옵션을 사용하여 시간 오차를 허용할 수 있습니다 (예: leeway=10).
        )
        print("ID Token successfully verified.")
        print("Payload:", payload)

        # --- 관리자 권한 확인 (커스텀 클레임 기반) ---
        # 검증된 페이로드에서 관리자 클레임을 확인합니다.
        if payload.get(ADMIN_CLAIM_NAME) is True:
            print("User is an administrator.")
            return payload
        else:
            print("User is NOT an administrator. Access denied.")
            # 관리자가 아닌 경우 특정 예외 발생
            raise PermissionError("Admin privilege required.")

    except jwt.ExpiredSignatureError:
        print("ID Token has expired.")
        raise jwt.ExpiredSignatureError("ID Token has expired.")
    except jwt.InvalidAudienceError:
        print(f"Invalid Audience. Expected: {AUDIENCE}")
        raise jwt.InvalidAudienceError(f"Invalid Audience. Expected: {AUDIENCE}")
    except jwt.InvalidIssuerError:
        print(f"Invalid Issuer. Expected: {ISSUER}")
        raise jwt.InvalidIssuerError(f"Invalid Issuer. Expected: {ISSUER}")
    except jwt.InvalidSignatureError:
        print("ID Token signature is invalid.")
        raise jwt.InvalidSignatureError("ID Token signature is invalid.")
    except jwt.DecodeError as e:
        print(f"Error decoding ID Token: {e}")
        raise jwt.DecodeError(f"Error decoding ID Token: {e}")
    except PermissionError:
         # 관리자 권한 없음 예외는 여기서 다시 발생시킵니다.
         raise
    except Exception as e:
        # 예상치 못한 다른 모든 오류 처리
        print(f"An unexpected error occurred during token verification: {e}")
        raise Exception(f"Token verification failed due to an unexpected error: {e}")


# --- 사용 예시 ---
# 실제 애플리케이션에서는 HTTP 요청에서 토큰을 추출하여 이 함수를 호출합니다.

# 예시: 가상의 ID 토큰 (실제 유효한 토큰으로 테스트해야 함)
# test_id_token_valid_admin = "..." # 유효하고 admin 클레임이 있는 토큰
# test_id_token_valid_user = "..." # 유효하고 admin 클레임이 없는 토큰
# test_id_token_expired = "..." # 만료된 토큰
# test_id_token_invalid_sig = "..." # 서명이 잘못된 토큰

# 토큰 검증 및 관리자 확인 시도
# try:
#     # 예시: 관리자 권한이 필요한 요청 처리
#     payload = verify_id_token_and_check_admin(test_id_token_valid_admin)
#     print("Successfully verified and authorized admin user.")
#     # 관리자 전용 로직 실행
#
# except (ValueError, jwt.PyJWTError, PermissionError, Exception) as e:
#     print(f"Request failed: {e}")
#     # 클라이언트에게 에러 응답 반환 (예: Flask/Django에서 401 Unauthorized 또는 403 Forbidden)

# # 다른 토큰으로 테스트 (주석 해제하여 테스트)
# try:
#     payload = verify_id_token_and_check_admin(test_id_token_valid_user)
#     print("Successfully verified non-admin user.") # 이 줄은 실행되지 않고 PermissionError 발생
# except (ValueError, jwt.PyJWTError, PermissionError, Exception) as e:
#     print(f"Request failed as expected for non-admin: {e}")
#     # 403 Forbidden 응답 반환
