from flask import request, jsonify

def admin_required(func):
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "Authorization header missing"}), 401

        parts = auth_header.split()
        if parts[0].lower() != 'bearer':
            return jsonify({"message": "Authorization header must be Bearer"}), 401
        elif len(parts) == 1:
            return jsonify({"message": "Token not found"}), 401
        elif len(parts) > 2:
            return jsonify({"message": "Authorization header must be Bearer token"}), 401

        id_token = parts[1]

        try:
            # 토큰 검증 및 관리자 권한 확인
            payload = verify_id_token_and_check_admin(id_token)
            # 검증 성공 시, 필요하다면 payload를 요청 컨텍스트에 저장
            # request.user_payload = payload
            return func(*args, **kwargs) # 원래 요청 핸들러 실행

        except (ValueError, jwt.PyJWTError, Exception) as e:
            # 토큰 검증 또는 일반 오류
            status_code = 401 # Unauthorized
            print(f"Auth error: {e}")
            # 에러 유형에 따라 더 상세한 상태 코드 반환 가능
            # if isinstance(e, PermissionError):
            #     status_code = 403 # Forbidden
            # elif isinstance(e, jwt.ExpiredSignatureError):
            #     status_code = 401 # or 400 Bad Request, depending on API design
            # ...

            return jsonify({"message": f"Authentication or Authorization failed: {e}"}), status_code
        except PermissionError as e:
             # 관리자 권한 없음 오류
             print(f"Permission error: {e}")
             return jsonify({"message": f"Authorization failed: {e}"}), 403 # Forbidden


    wrapper.__name__ = func.__name__ # 데코레이터 사용 시 함수 이름 유지를 위해 필요
    return wrapper

# Flask 애플리케이션 라우트 예시
# @app.route('/admin/resource')
# @admin_required
# def admin_resource():
#     # 이 함수는 토큰 검증 및 관리자 권한 확인을 통과한 요청에 대해서만 실행됩니다.
#     return jsonify({"message": "Welcome, Admin!"})
