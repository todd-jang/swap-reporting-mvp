# my_app/tests/test_integration.py

from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status # DRF 상태 코드 사용

# 우리가 테스트할 뷰 함수 및 인증 로직 임포트
# from my_app.views import AdminOnlyAPIView
# from my_django_project.auth.token_verification import verify_id_token_and_check_admin, AdminPrivilegeRequiredError

# unittest.mock 사용하여 외부 의존성 모의
from unittest.mock import patch, MagicMock

class AuthenticationIntegrationTests(TestCase):
    """
    AdminOnlyAPIView 뷰와 인증 로직의 연동에 대한 통합 테스트.
    Django 테스트 클라이언트를 사용하여 HTTP 요청/응답을 시뮬레이션합니다.
    JWKS 가져오기 등 외부 네트워크 호출은 모의합니다.
    """

    def setUp(self):
        """각 테스트 메소드 실행 전 설정."""
        self.client = Client()
        # 테스트할 API 엔드포인트 URL 이름
        self.admin_api_url = reverse('admin_api') # my_app/urls.py에 정의된 이름


    # verify_id_token_and_check_admin 함수 자체를 모의하여 통합 테스트 수행
    # 실제 이 함수 내부 로직은 test_unit.py에서 테스트됨. 여기서는 호출 결과에 따른 뷰의 동작 테스트.
    @patch('my_app.views.verify_id_token_and_check_admin') # 뷰 함수 내에서 호출되는 인증 함수를 모의
    def test_admin_api_access_with_admin_token(self, mock_verify_admin):
        """유효한 관리자 토큰으로 관리자 API 접근 시 200 응답을 받는지 테스트."""
        # 인증 함수가 성공하고 관리자 페이로드를 반환하도록 설정
        mock_verify_admin.return_value = {"sub": "admin_user", "admin": True, "iss": "...", "aud": "...", "exp": ...}

        # 테스트용 유효 토큰 (실제 검증은 모의 객체가 처리)
        admin_token = "fake_valid_admin_token"
        # Django 테스트 클라이언트는 HTTP 헤더를 'HTTP_' 접두사를 붙여 전달합니다.
        headers = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}

        # GET 요청 시뮬레이션
        response = self.client.get(self.admin_api_url, **headers)

        # 응답 상태 코드 검증
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 응답 내용 검증 (선택 사항)
        # self.assertEqual(response.json()['message'], "Welcome to the admin API!")

        # verify_id_token_and_check_admin 함수가 올바른 토큰으로 호출되었는지 검증
        mock_verify_admin.assert_called_once_with(admin_token)


    @patch('my_app.views.verify_id_token_and_check_admin')
    def test_admin_api_access_with_non_admin_token(self, mock_verify_admin):
        """관리자 권한이 없는 유효 토큰으로 관리자 API 접근 시 403 Forbidden 응답을 받는지 테스트."""
        # 인증 함수가 AdminPrivilegeRequiredError 예외를 발생시키도록 설정
        mock_verify_admin.side_effect = AdminPrivilegeRequiredError("Admin privilege required.")

        non_admin_token = "fake_valid_user_token"
        headers = {'HTTP_AUTHORIZATION': f'Bearer {non_admin_token}'}

        response = self.client.get(self.admin_api_url, **headers)

        # 응답 상태 코드 검증 (403 Forbidden)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # 응답 내용 검증 (선택 사항)
        # self.assertEqual(response.json()['detail'], "You do not have permission to perform this action.")


    @patch('my_app.views.verify_id_token_and_check_admin')
    def test_admin_api_access_without_token(self, mock_verify_admin):
        """Authorization 헤더 없이 관리자 API 접근 시 401 Unauthorized 응답을 받는지 테스트."""
        # Authorization 헤더를 보내지 않음
        response = self.client.get(self.admin_api_url)

        # 응답 상태 코드 검증 (401 Unauthorized)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 응답 내용 검증 (선택 사항)
        # self.assertEqual(response.json()['detail'], "Authentication credentials were not provided.")

        # 인증 함수가 호출되지 않았는지 확인 (Authorization 헤더 검사 전에 차단되므로)
        mock_verify_admin.assert_not_called()


    @patch('my_app.views.verify_id_token_and_check_admin')
    def test_admin_api_access_with_expired_token(self, mock_verify_admin):
        """만료된 토큰으로 관리자 API 접근 시 401 Unauthorized 응답을 받는지 테스트."""
        # 인증 함수가 jwt.ExpiredSignatureError 예외를 발생시키도록 설정
        mock_verify_admin.side_effect = jwt.ExpiredSignatureError("Token has expired.")

        expired_token = "fake_expired_token"
        headers = {'HTTP_AUTHORIZATION': f'Bearer {expired_token}'}

        response = self.client.get(self.admin_api_url, **headers)

        # 응답 상태 코드 검증 (401 Unauthorized)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # 응답 내용 검증 (선택 사항)
        # self.assertIn("Token has expired", response.json()['detail'])


    # TODO: 여기에 다른 통합 테스트 케이스 작성 (예: 잘못된 Authorization 헤더 형식, 잘못된 서명 토큰, 잘못된 Audience/Issuer 등)
