
# swap_reporting_mvp/ui_backend/Dockerfile

# Docker 컨테이너화 예시 (FastAPI 앱 가정)
FROM python:3.9-slim # 가벼운 Python 이미지 사용

WORKDIR /app # 컨테이너 내 작업 디렉터리 설정

# 의존성 파일만 먼저 복사하여 빌드 캐싱 활용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 나머지 애플리케이션 코드 복사
# setup.py를 사용한다면, 여기서 setup.py와 ui_backend/ 디렉터리를 복사하고
# RUN pip install . 으로 설치하는 방식을 사용할 수도 있습니다.
COPY ui_backend/ /app/ui_backend/
COPY .env /app/.env # 환경 변수 파일 복사 (보안 주의: Secrets Manager 권장)

# 필요한 포트 노출 (FastAPI 기본 포트 8000 가정)
EXPOSE 8000

# 애플리케이션 실행 명령어 (uvicorn 사용 예시)
# ui_backend/api.py 파일에 FastAPI 앱 객체 'app'이 있다고 가정
CMD ["uvicorn", "ui_backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
