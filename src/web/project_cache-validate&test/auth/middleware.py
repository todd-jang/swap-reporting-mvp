# my_project/middleware.py 또는 my_project/views.py 에서

from my_project.auth.token_verification import verify_id_token_and_check_admin
# from my_project.auth.middleware import admin_required # 데코레이터를 auth/middleware.py에 정의했다면

# 이제 verify_id_token_and_check_admin 함수를 사용할 수 있습니다.
# ... (위의 코드 예시 참고)
