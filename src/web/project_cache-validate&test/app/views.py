# my_app/views.py

from django.http import JsonResponse, HttpResponseForbidden
from rest_framework.views import APIView # DRF를 사용한다면
from rest_framework.response import Response
from rest_framework import status

# 우리가 만든 인증 로직 임포트
from my_django_project.auth.token_verification import verify_id_token_and_check_admin, AdminPrivilegeRequiredError
import jwt # jwt 예외 처리를 위해 임포트

# Django REST Framework (DRF)를 사용하지 않는 일반 Django 뷰 예시
# from django.views import View
# class AdminOnlyView(View):
#     def get(self, request, *args, **kwargs):
#         auth_header = request.headers.get('Authorization')
#         if not auth_header:
#             return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)
#
#         parts = auth_header.split()
#         if parts[0].lower() != 'bearer' or len(parts) != 2:
#             return JsonResponse({"detail": "Authorization header must be Bearer token."}, status=401)
#
#         id_token = parts[1]
#
#         try:
#             # 토큰 검증 및 관리자 확인 함수 호출
#             payload = verify_id_token_and_check_admin(id_token)
#             # 검증 및 관리자 확인 성공 시
#             # payload를 사용하여 사용자 정보를 활용할 수 있습니다.
#             return JsonResponse({"message": "Welcome to the admin area!", "user": payload.get('sub')})
#
#         except (ValueError, jwt.PyJWTError, Exception) as e:
#             # 토큰 검증 중 오류 발생 (JWT 관련, 키 가져오기 오류 등)
#             # jwt.PyJWTError의 하위 클래스들은 401 Unauthorized에 해당
#             # 그 외 Exception은 500 Internal Server Error 등으로 처리 가능
#             status_code = status.HTTP_401_UNAUTHORIZED # 401
#             # 오류 유형에 따라 더 구체적인 메시지 제공 가능
#             if isinstance(e, jwt.ExpiredSignatureError):
#                 detail = "Token has expired."
#             elif isinstance(e, jwt.InvalidSignatureError):
#                  detail = "Token signature is invalid."
#             else:
#                  detail = str(e) # 또는 일반적인 인증 실패 메시지
#
#             return JsonResponse({"detail": f"Authentication failed: {detail}"}, status=status_code)
#
#         except AdminPrivilegeRequiredError:
#             # 관리자 권한 없음 오류 발생 시
#             return HttpResponseForbidden("Admin privilege required.") # 403 Forbidden 응답

# Django REST Framework (DRF)를 사용하는 경우 (더 일반적)
# APIView 또는 ViewSet 사용
class AdminOnlyAPIView(APIView):
    """
    관리자만 접근 가능한 API 엔드포인트.
    """
    def get(self, request, *args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            # DRF의 Response와 status 코드를 사용합니다.
            return Response({"detail": "Authentication credentials were not provided."}, status=status.HTTP_401_UNAUTHORIZED)

        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return Response({"detail": "Authorization header must be Bearer token."}, status=status.HTTP_401_UNAUTHORIZED)

        id_token = parts[1]

        try:
            # 토큰 검증 및 관리자 확인 함수 호출
            payload = verify_id_token_and_check_admin(id_token)
            # 검증 및 관리자 확인 성공 시
            # payload를 request.user 등으로 설정하여 DRF 기본 인증 시스템과 통합할 수도 있습니다.
            # 여기서는 간단히 메시지와 페이로드를 반환합니다.
            return Response({"message": "Welcome to the admin API!", "user": payload.get('sub'), "payload": payload}, status=status.HTTP_200_OK)

        except (ValueError, jwt.PyJWTError, Exception) as e:
            # 토큰 검증 중 오류 발생
            status_code = status.HTTP_401_UNAUTHORIZED # 401

            # 오류 유형에 따라 더 상세한 메시지 제공
            detail = f"Authentication failed: {e}"
            if isinstance(e, jwt.ExpiredSignatureError):
                detail = "Authentication failed: Token has expired."
            elif isinstance(e, jwt.InvalidSignatureError):
                 detail = "Authentication failed: Token signature is invalid."
            # ... 다른 jwt.PyJWTError 하위 클래스에 대한 처리 추가 가능

            return Response({"detail": detail}, status=status_code)

        except AdminPrivilegeRequiredError:
            # 관리자 권한 없음 오류 발생 시
            return Response({"detail": "You do not have permission to perform this action."}, status=status.HTTP_403_FORBIDDEN) # 403 Forbidden 응답
