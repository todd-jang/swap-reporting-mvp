# my_app/tests/test_performance.py

from django.test import TestCase
from django.urls import reverse
from django.test import Client # API 호출 성능 테스트를 위해
import time
# 필요한 모듈 임포트 및 모의 설정 (test_unit.py 참고)
from unittest.mock import patch, MagicMock
import jwt # 예외 임포트


# test_unit.py와 유사하게 인증 로직 및 외부 의존성을 모의합니다.
# 성능 측정 대상 코드가 순수 Python 함수라면 모의만 사용.
# API 호출 성능이라면 Django Client 사용 시 외부 호출 (JWKS) 모의 필요.

# verify_id_token_and_check_admin 함수를 모의하여 순수 로직 성능 측정 시
# @patch('my_django_project.auth.token_verification.jwt.decode', MagicMock())
# @patch('my_django_project.auth.token_verification.jwk_client', MagicMock())
# @patch('my_django_project.auth.token_verification.settings', MagicMock())
class PerformanceTests(TestCase):
    """
    애플리케이션의 특정 부분에 대한 기본적인 성능 테스트.
    종합적인 부하 테스트는 외부 도구를 사용합니다.
    """

    def setUp(self):
         # test_unit.py와 유사하게 settings, jwk_client, jwt.decode 등을 모의 설정합니다.
         # 순수 로직 성능 측정을 위해 외부 의존성 모의가 중요합니다.
         # API 호출 성능 측정 시에는 Django Client를 사용하고 verify_id_token_and_check_admin 함수 자체를 모의할 수 있습니다.
         pass


    # 예시: 토큰 검증 함수 자체의 순수 로직 처리 시간 측정 (외부 호출 제외)
    # 모의 설정을 통해 jwt.decode, JWK 가져오기 등을 모의합니다.
    # def test_token_verification_logic_performance(self):
    #     """모의 환경에서 verify_id_token_and_check_admin 함수의 순수 로직 처리 시간 측정."""
    #     # 모의된 jwt.decode가 반환할 페이로드 설정
    #     payload = {"iss": "...", "aud": "...", "exp": int(time.time()) + 3600, "sub": "test", "admin": True}
    #     # self.mock_jwt_decode.return_value = payload # setUp에서 설정된 mock_jwt_decode 사용
    #
    #     num_runs = 1000 # 반복 횟수 늘림
    #     token = "fake_token"
    #
    #     start_time = time.time()
    #     for _ in range(num_runs):
    #         try:
    #             # 모의된 verify_id_token_and_check_admin 함수 호출
    #             # verify_id_token_and_check_admin(token)
    #             pass # 실제 함수 호출 코드로 교체
    #         except Exception:
    #             pass # 성능 측정 목적이므로 예외 발생 시 실패 처리하지 않음
    #
    #     end_time = time.time()
    #     average_time_ms = ((end_time - start_time) / num_runs) * 1000
    #
    #     print(f"\nAverage token verification logic time ({num_runs} runs): {average_time_ms:.4f} ms")
    #     # 특정 임계값보다 빨라야 함 (밀리초 단위)
    #     # self.assertLess(average_time_ms, 1.0) # 예: 1ms 미만


    # 예시: Django 테스트 클라이언트를 사용한 API 엔드포인트 응답 시간 측정 (경량 부하)
    # 이 경우 verify_id_token_and_check_admin 함수 자체를 모의하여 JWKS 외부 호출 지연을 제거하고
    # 뷰, 미들웨어, 내부 로직의 성능만 측정할 수 있습니다.
    # @patch('my_app.views.verify_id_token_and_check_admin') # 뷰에서 호출되는 인증 함수 모의
    # def test_admin_api_response_time_simulated_auth(self, mock_verify_admin):
    #     """모의 인증 통과 시 Admin API 응답 시간 측정."""
    #     client = Client()
    #     url = reverse('admin_api') # 테스트 대상 URL
    #
    #     # 인증 함수가 항상 성공하고 관리자 페이로드를 반환하도록 설정
    #     mock_verify_admin.return_value = {"sub": "admin_user", "admin": True, "iss": "...", "aud": "...", "exp": ...}
    #
    #     admin_token = "fake_token"
    #     headers = {'HTTP_AUTHORIZATION': f'Bearer {admin_token}'}
    #
    #     num_requests = 100 # 요청 횟수
    #     response_times = []
    #
    #     start_time = time.time()
    #     for _ in range(num_requests):
    #         response = client.get(url, **headers)
    #         self.assertEqual(response.status_code, 200) # 응답 상태 코드 확인
    #     end_time = time.time()
    #
    #     total_time_ms = (end_time - start_time) * 1000
    #     average_response_time = total_time_ms / num_requests
    #
    #     print(f"\nAverage Admin API response time with mocked auth ({num_requests} requests): {average_response_time:.2f} ms")
    #     # self.assertLess(average_response_time, 50) # 예: 50ms 미만


    # TODO: 여기에 코드 레벨 성능 측정 테스트 추가
    pass
