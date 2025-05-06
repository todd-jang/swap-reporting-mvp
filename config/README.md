1. 배포본 만들기 (Packaging)

여러분의 Python 코드를 배포 가능한 형태로 만드는 과정입니다.

의존성 관리: 프로젝트에서 사용하는 모든 Python 패키지 목록을 requirements.txt 파일에 명시합니다.

Plaintext

# swap_reporting_mvp/requirements.txt
Django # 또는 FastAPI 등 여러분의 웹 프레임워크
PyJWT
PyJWK
requests
python-decouple
dj_database_url # Django + DATABASE_URL 환경 변수 사용 시
psycopg2-binary # PostgreSQL 드라이버
gunicorn # 또는 uwsgi (WSGI 서버)
uvicorn # ASGI 서버 (FastAPI 등)
pytest
pytest-mock
selenium
webdriver-manager
# TODO: 프로젝트의 모든 의존성 추가
이 파일은 pip freeze > requirements.txt 명령으로 생성하거나 수동으로 관리합니다.

애플리케이션 코드: .py 파일들, 템플릿 파일, 정적 파일 등 실행에 필요한 모든 코드를 포함합니다.

설정 파일: settings.py (Django) 또는 .env 파일 등 환경별 설정 정보 관리 파일을 포함합니다.

(옵션) 패키징: setup.py 또는 pyproject.toml을 사용하여 프로젝트를 설치 가능한 Python 패키지로 만들 수 있습니다 (.whl 파일 등). 이는 코드 재사용이나 복잡한 프로젝트 구조에서 유용할 수 있습니다.

Python

# swap_reporting_mvp/setup.py
from setuptools import setup, find_packages

setup(
    name='swap_reporting_mvp',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        # requirements.txt 내용과 동일하게 또는 필요한 핵심 의존성만
        'Django',
        'PyJWT',
        # ...
    ],
    # 기타 메타데이터
)
pip install . 또는 pip wheel . 명령으로 패키징합니다.

2. VM에 Patch 배포 (Direct Deployment)

컨테이너나 오케스트레이션 없이 NCP VM에 직접 애플리케이션 코드를 배포하고 실행하는 방법입니다.

VM 준비: Python 환경, pip 설치.

코드 전송: SCP, SFTP 또는 Git Clone을 사용하여 VM으로 코드 전송.

의존성 설치: VM에서 pip install -r requirements.txt 실행.

설정: .env 파일 생성 또는 환경 변수 설정 (NCP 콘솔 또는 /etc/environment).

WSGI/ASGI 서버 설치: gunicorn 또는 uvicorn 설치.

서비스 관리: systemd 스크립트를 작성하여 애플리케이션 프로세스(Gunicorn/uvicorn)를 관리합니다 (자동 시작, 재시작, 로깅).

Ini, TOML

# /etc/systemd/system/vb_api_svr.service (예시)
[Unit]
Description=Gunicorn instance to serve Vb API Svr
After=network.target

[Service]
User=your_user # VM에서 실행할 사용자
Group=your_group # VM에서 실행할 그룹
WorkingDirectory=/path/to/your/project # 프로젝트 코드가 있는 경로
Environment="PATH=/path/to/your/venv/bin" # 가상 환경 경로 설정
# EnvironmentFile=/path/to/your/project/.env # .env 파일 사용 시
ExecStart=/path/to/your/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 vb_api_svr.main:app # Gunicorn 실행 명령어 (프로젝트 구조 및 WSGI/ASGI 앱 객체 이름에 맞게 수정)

[Install]
WantedBy=multi-user.target
systemctl daemon-reload, systemctl enable vb_api_svr.service, systemctl start vb_api_svr.service 명령으로 서비스 등록 및 시작.

웹 서버 (Nginx/Apache): VM에 Nginx 설치 후 리버스 프록시로 구성하여 클라이언트 요청을 Gunicorn/uvicorn으로 전달하고 정적 파일을 서빙합니다.

Nginx

# /etc/nginx/sites-available/vb_api_svr (예시)
server {
    listen 80;
    server_name your_vb_api_domain_or_ip;

    location / {
        proxy_pass http://127.0.0.1:8000; # Gunicorn/uvicorn 포트
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 정적 파일 서빙 (프론트엔드 또는 백엔드 정적 파일)
    # location /static/ {
    #     alias /path/to/your/project/staticfiles/; # collectstatic으로 모인 경로
    # }
}
사이트 활성화 및 Nginx 재시작.

배포 자동화: 수동 전송/설정 대신 Jenkins, GitLab CI, GitHub Actions 등 CI/CD 도구에서 SSH 연결을 통해 원격으로 코드 전송, 의존성 설치, 서비스 재시작 등의 작업을 자동화합니다.

3. 컨테이너화 (Docker)

각 구성 요소를 독립적인 컨테이너 이미지로 만듭니다. 이는 배포 및 오케스트레이션을 위한 현대적인 방식입니다.

Dockerfile: 각 구성 요소별로 Dockerfile을 작성합니다.

Dockerfile

# swap_reporting_mvp/vb_api_svr/Dockerfile (예시: FastAPI 앱)
FROM python:3.9-slim # 베이스 이미지 (필요한 Python 버전 선택)

WORKDIR /app # 작업 디렉터리 설정

COPY requirements.txt . # 의존성 파일 복사 (캐싱 활용을 위해 먼저)
RUN pip install --no-cache-dir -r requirements.txt # 의존성 설치

COPY . . # 현재 디렉터리의 모든 파일 복사 (여러분의 코드)

# 필요한 포트 노출 (FastAPI 기본 포트)
EXPOSE 8000

# 애플리케이션 실행 명령어 (uvicorn 사용 예시)
# vb_api_svr/main.py 파일에 app 객체가 있다고 가정
CMD ["uvicorn", "vb_api_svr.main:app", "--host", "0.0.0.0", "--port", "8000"]
docker build -t vb_api_svr:latest . 명령으로 이미지를 빌드합니다.

Container Registry: 빌드된 이미지를 NCP Container Registry와 같은 레지스트리에 Push 하여 관리합니다.

4. 컨테이너 오케스트레이션 및 배포 자동화

여러 개의 컨테이너화된 구성 요소를 정의하고 실행하며 관리하는 방법입니다.

Docker Compose (docker-compose.yml): 개발, 테스트 환경 또는 소규모 MVP 배포에 적합합니다. 여러 서비스를 하나의 YAML 파일에 정의하고 관리합니다.

YAML

# swap_reporting_mvp/docker-compose.yml (예시)
version: '3.8'

services:
  vb_api_svr:
    build: ./vb_api_svr # Dockerfile 위치
    ports:
      - "8000:8000" # 호스트 포트:컨테이너 포트
    volumes:
      - .env:/app/.env # .env 파일을 컨테이너 내부로 마운트
    env_file:
      - .env # 또는 이렇게 환경 변수 로드
    # environment: # 또는 직접 환경 변수 설정
    #   SECRET_KEY: ${SECRET_KEY}
    #   DATABASE_URL: ${DATABASE_URL}

  vo_api_svr:
    build: ./vo_api_svr
    ports:
      - "8001:8001" # Vo api svr 포트 가정
    volumes:
      - .env:/app/.env
    env_file:
      - .env

  tain_tube:
    build: ./tain_tube
    volumes:
      - /data:/data # 데이터 디렉터리 마운트 (호스트와 공유)
      - .env:/app/.env
    env_file:
      - .env
    # command: python tain_tube/runner.py # 실행 명령어 (필요시)

  tain_bat:
    build: ./tain_bat
    volumes:
      - /data:/data # 데이터 디렉터리 마운트
      - .env:/app/.env
    env_file:
      - .env
    # command: python tain_bat/scheduler.py # 실행 명령어 (필요시)

  tain_on:
    build: ./tain_on
    volumes:
      - .env:/app/.env
    env_file:
      - .env
    # command: python tain_on/realtime_listener.py # 실행 명령어 (필요시)

  # db: # 테스트/개발용 DB 컨테이너 정의 예시 (프로덕션 Cloud DB와 다름)
  #   image: postgres:13
  #   volumes:
  #     - db_data:/var/lib/postgresql/data
  #   environment:
  #     POSTGRES_DB: ${DB_NAME}
  #     POSTGRES_USER: ${DB_USER}
  #     POSTGRES_PASSWORD: ${DB_PASSWORD}

# volumes: # DB 데이터 영속성을 위한 볼륨 정의
#   db_data:

docker-compose up -d 명령으로 서비스를 실행합니다.

Kubernetes (.yaml): 프로덕션 환경에 적합한 확장성, 가용성, 관리 기능을 제공합니다. NCP Kubernetes Service에서 사용합니다. 각 구성 요소를 Pod, Deployment, Service 등으로 정의합니다.

YAML

# swap_reporting_mvp/k8s/vb-api-deployment.yaml (예시)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vb-api-svr
spec:
  replicas: 3 # 인스턴스(Pod) 개수
  selector:
    matchLabels:
      app: vb-api-svr
  template:
    metadata:
      labels:
        app: vb-api-svr
    spec:
      containers:
      - name: vb-api-svr
        image: YOUR_NCP_CONTAINER_REGISTRY/vb_api_svr:latest # NCP Container Registry 이미지 경로
        ports:
        - containerPort: 8000
        env: # 환경 변수 설정
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef: # Kubernetes Secret 사용 (보안 권장)
              name: swap-reporting-secrets
              key: secret_key
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: swap-reporting-secrets
              key: database_url
        # TODO: 다른 환경 변수 설정

---
# swap_reporting_mvp/k8s/vb-api-service.yaml (예시)
apiVersion: v1
kind: Service
metadata:
  name: vb-api-svr
spec:
  selector:
    app: vb-api-svr
  ports:
  - protocol: TCP
    port: 80 # 외부 노출 포트
    targetPort: 8000 # 컨테이너 포트
  type: LoadBalancer # NCP Load Balancer 연동
  # 또는 ClusterIP (내부 사용) 또는 NodePort

# TODO: 다른 구성 요소 (vo-api-svr, tain-tube 등)에 대한 Deployment, Service, ConfigMap, Secret, PersistentVolumeClaim YAML 파일 작성
# TODO: TainTube, TainBat 등은 CronJob, StatefulSet 등으로 정의될 수 있습니다.
kubectl apply -f swap_reporting_mvp/k8s/ 명령으로 배포합니다.

배포 자동화 (CI/CD): Jenkins, GitLab CI, GitHub Actions, NCP Cloud Insight (Monitoring & Alerting), NCP Cloud Log Analytics 등을 연동하여 코드 변경 감지 -> 테스트 실행 -> Docker 이미지 빌드 -> Container Registry Push -> Kubernetes (또는 VM) 배포 -> 모니터링/로깅 연동까지 자동화된 파이프라인을 구축합니다.

5. 구성 파일 타입 (.yml, .toml 등)

.yml / .yaml: Docker Compose, Kubernetes manifests 등 컨테이너 오케스트레이션 정의에 널리 사용됩니다. 구조화된 설정 정보를 표현하기에 좋습니다.
.toml: 설정 파일 형식 중 하나로, .ini 파일보다 표현력이 좋습니다. python-decouple과 같은 라이브러리에서 .env 파일을 대체하거나 애플리케이션 자체의 복잡한 설정 파일로 사용할 수 있습니다. (예: settings.toml)
.env: 환경 변수를 .ini 형식으로 저장하는 간단한 파일입니다. 개발 환경에서 환경 변수 로드에 편리하게 사용됩니다. 프로덕션에서는 시스템 환경 변수나 Secrets Manager 사용이 더 안전합니다.
PostgreSQL 및 프론트엔드 연동 완성본 (NCP 기준):

PostgreSQL: NCP Cloud DB for PostgreSQL 인스턴스를 프로덕션 환경에 맞게 HA(고가용성) 구성으로 생성합니다. 백엔드 서비스들은 이 Cloud DB의 내부 Private IP와 포트(5432)로 연결하며, 필요한 ACG/NACL 규칙을 설정합니다. 데이터베이스 연결 정보는 Secrets Manager를 통해 안전하게 관리하고 애플리케이션이 로드 시 이를 사용하도록 구현합니다.
프론트엔드 (TainWeb): SPA (Single Page Application)라면 빌드된 정적 파일(HTML, CSS, JS)을 NCP Object Storage에 업로드하고 NCP CDN 서비스를 연결하여 서빙합니다. 백엔드 API 호출은 NCP API Gateway의 URL을 통해 이루어지도록 프론트엔드 코드를 설정합니다. API Gateway는 /api/* 경로의 요청을 백엔드 API 서버(Vb api svr, Vo api svr)로 라우팅합니다.
MVP와 프로덕션 완성본 구축 요약:

MVP: VM 직접 배포 또는 Docker Compose를 사용하여 단일 서버에 통합 배포. NCP Cloud DB 소규모 인스턴스 사용. Nginx 리버스 프록시 또는 간단한 API Gateway 설정.
프로덕션: 각 구성 요소를 Docker 컨테이너로 분리. NCP Kubernetes Service에 배포하여 오케스트레이션. NCP Cloud DB HA 구성. NCP API Gateway Service 사용. 정적 파일은 Object Storage+CDN으로 서빙. NCP Secrets Manager로 민감 정보 관리. Cloud Watch, Cloud Log Analytics로 모니터링/로깅 통합. CI/CD 파이프라인 구축.
