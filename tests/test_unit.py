# my_app/tests/test_unit.py

from django.test import TestCase
# unittest.mock 을 사용하여 외부 라이브러리 호출을 모의(Mock)합니다.
from unittest.mock import patch, MagicMock
import jwt
import time # 시간 관련 테스트를 위해

# 우리가 테스트할 함수를 포함하는 모듈 임포트
# 실제 여러분의 프로젝트 구조에 맞게 임포트 경로를 수정해야 합니다.
# from my_django_project.auth.token_verification import verify_id_token_and_check_admin, AdminPrivilegeRequiredError
# from my_django_project.auth import token_verification # 모듈 자체를 임포트하여 모의할 때

# 예시를 위해 함수를 직접 정의하거나, 실제 임포트 경로 사용
class AdminPrivilegeRequiredError(PermissionError): pass

# 임시 함수 정의 (여러분의 실제 verify_id_token_and_check_admin 함수로 대체)
# @patch('my_django_project.auth.token_verification.jwk_client', MagicMock()) # 모듈 레벨 jwk_client를 모의
# @patch('my_django_project.auth.token_verification.settings', MagicMock()) # settings를 모의
def verify_id_token_and_check_admin(id_token: str):
    """
    이 함수는 테스트를 위한 임시 함수입니다.
    실제 여러분의 프로젝트에 있는 verify_id_token_and_check_admin 함수로 교체하세요.
    """
    # 모의 객체로 대체될 jwt.decode 호출
    # 실제 테스트에서는 이 부분이 모의됩니다.
    payload = jwt.decode(id_token, "fake_key", algorithms=["RS256"], options={"verify_signature": False}) # 서명 검증 생략

    # 임시로 관리자 클레임만 확인하는 로직
    if payload.get("admin") is True:
        return payload
    else:
        raise AdminPrivilegeRequiredError("Admin privilege required.")


class AuthenticationUnitTests(TestCase):
    """
    인증 로직 (verify_id_token_and_check_admin) 에 대한 단위 테스트.
    외부 의존성 (jwt 라이브러리, JWK 클라이언트, settings) 을 모의(Mock)하여 테스트.
    """

    # 테스트 시작 전에 공통적으로 사용할 모의 객체 설정
    # patch 데코레이터는 setUp/tearDown에서 설정하는 것보다 편리할 수 있습니다.
    # 테스트 대상 함수가 속한 모듈 경로에 맞게 'my_django_project.auth.token_verification' 부분을 수정하세요.
    @patch('my_django_project.auth.token_verification.jwt.decode')
    @patch('my_django_project.auth.token_verification.jwk_client', MagicMock()) # 모듈 레벨 jwk_client 모의
    @patch('my_django_project.auth.token_verification.settings', MagicMock()) # settings 모의
    def setUp(self, mock_settings, mock_jwk_client, mock_jwt_decode):
        """각 테스트 메소드 실행 전 모의 객체를 설정합니다."""
        # settings 모의 객체에 필요한 속성 설정
        mock_settings.AUTH_AUDIENCE = "YOUR_AUDIENCE"
        mock_settings.AUTH_ISSUER = "YOUR_ISSUER"
        mock_settings.AUTH_ADMIN_CLAIM_NAME = "admin"
        mock_settings.AUTH_TOKEN_ALGORITHMS = ["RS256"]
        mock_settings.AUTH_JWKS_URL = "fake_url" # JWKS URL 설정 (실제 호출은 모의됨)

        # jwk_client 모의 객체의 필요한 메소드 모의 (예: get_signing_key_from_jwt)
        mock_signing_key = MagicMock()
        mock_signing_key.public_key = "fake_public_key" # 모의 공개 키
        mock_jwk_client.get_signing_key_from_jwt.return_value = mock_signing_key

        # jwt.decode 함수의 기본 동작을 모의합니다.
        # 각 테스트 케이스에서 필요에 따라 return_value 또는 side_effect를 오버라이드할 수 있습니다.
        self.mock_jwt_decode = mock_jwt_decode


    def test_valid_token_admin_true(self):
        """관리자 클레임이 True인 유효 토큰 검증 시 성공하고 페이로드를 반환하는지 테스트."""
        valid_admin_payload = {
            "iss": "YOUR_ISSUER",
            "aud": "YOUR_AUDIENCE",
            "exp": int(time.time()) + 3600, # 미래 시간
            "sub": "admin_user_123",
            "admin": True # 관리자 클레임
        }
        # jwt.decode가 이 페이로드를 반환하도록 설정
        self.mock_jwt_decode.return_value = valid_admin_payload

        token = "fake_valid_admin_token"
        payload = verify_id_token_and_check_admin(token) # 모의된 함수 호출

        # 결과 검증
        self.assertEqual(payload, valid_admin_payload)
        # jwt.decode가 올바른 인자로 호출되었는지 검증할 수 있습니다 (선택 사항)
        # self.mock_jwt_decode.assert_called_once_with(
        #     token,
        #     "fake_public_key", # 모의 공개 키
        #     algorithms=["RS256"],
        #     audience="YOUR_AUDIENCE",
        #     issuer="YOUR_ISSUER",
        #     options={"verify_signature": True, "verify_exp": True, "verify_aud": True, "verify_iss": True}
        # )


    def test_valid_token_admin_false(self):
        """관리자 클레임이 False인 유효 토큰 검증 시 AdminPrivilegeRequiredError가 발생하는지 테스트."""
        valid_user_payload = {
            "iss": "YOUR_ISSUER",
            "aud": "YOUR_AUDIENCE",
            "exp": int(time.time()) + 3600,
            "sub": "regular_user_456",
            "admin": False # 관리자 아님
        }
        self.mock_jwt_decode.return_value = valid_user_payload

        token = "fake_valid_user_token"

        # 특정 예외가 발생하는지 테스트
        with self.assertRaises(AdminPrivilegeRequiredError):
            verify_id_token_and_check_admin(token)


    def test_valid_token_no_admin_claim(self):
        """관리자 클레임이 아예 없는 유효 토큰 검증 시 AdminPrivilegeRequiredError가 발생하는지 테스트."""
        payload_no_admin = {
            "iss": "YOUR_ISSUER",
            "aud": "YOUR_AUDIENCE",
            "exp": int(time.time()) + 3600,
            "sub": "user_without_claim_789",
            # 'admin' 클레임 없음
        }
        self.mock_jwt_decode.return_value = payload_no_admin

        token = "fake_token_no_admin_claim"

        with self.assertRaises(AdminPrivilegeRequiredError):
            verify_id_token_and_check_admin(token)


    def test_expired_token_raises_error(self):
        """만료된 토큰 검증 시 jwt.ExpiredSignatureError가 발생하는지 테스트."""
        # jwt.decode 호출 시 ExpiredSignatureError 예외를 발생시키도록 설정
        self.mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token has expired.")

        token = "fake_expired_token"

        with self.assertRaises(jwt.ExpiredSignatureError):
            verify_id_token_and_check_admin(token)


    def test_invalid_signature_raises_error(self):
        """잘못된 서명을 가진 토큰 검증 시 jwt.InvalidSignatureError가 발생하는지 테스트."""
        self.mock_jwt_decode.side_effect = jwt.InvalidSignatureError("Signature verification failed.")

        token = "fake_invalid_signature_token"

        with self.assertRaises(jwt.InvalidSignatureError):
            verify_id_token_and_check_admin(token)

    # TODO: 여기에 다른 단위 테스트 케이스 작성 (예: 잘못된 Audience, 잘못된 Issuer, 토큰 문자열 없음 등)
