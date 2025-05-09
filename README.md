# Swap Reporting MVP

To run this locally, you would need to start each of the five modules (data-ingestion, data-processing, validation, report-generation, report-submission, error-monitoring, web) in separate terminals, ensuring they are listening on the ports specified in the httpx calls (8000, 8001, 8002, 8003, 8004, 8005, 8006).



# frontend Development Process:

Set up Frontend Project: Initialize a new project using your chosen framework's CLI (e.g., create-react-app, vue create, ng new).

Design UI/UX: Plan the layout, components, and user flow based on the required functionalities.

Implement Components: Build reusable UI components (tables, forms, buttons, charts).

Connect to Backend API: Implement the logic to fetch and send data to the /api/* endpoints using fetch or Axios.

Implement Routing: Set up client-side routing to navigate between different views (e.g., list errors, view error details).

Build and Test: Build the frontend application using your build tool and test it thoroughly in a local development environment, ensuring it correctly interacts with your running backend modules.

Integrate with Backend Serving: Configure your build process to output the static files into the src/web/static/ directory so the web module can serve them.


#시스템 구성 요소 (다이어그램 기반):

입력 FEPs: Vb fep, Vo fep (데이터 수집 시작점, On-premise 또는 외부 클라우드에 위치할 수 있음)
데이터 수집/적재: TainTube (파일 기반), TainOn (스트림 기반 초기 처리)
데이터 처리: TainBat (배치), TainOn (온라인/온디맨드)
데이터 저장소: DB (PostgreSQL - NCP Cloud DB), 파일 시스템 (/data/... 디렉터리)
API 서비스: Vb api svr, Vo api svr (백엔드 API)
웹 UI: TainWeb (프론트엔드 서버/클라이언트)
외부 전송: Vo fep (처리된 데이터 외부 전송)
API 진입점: API Gateway (외부 트래픽 첫 진입점)
인증: JWT 기반 (jwt 로 표현)
통합 연동 지점 및 NCP 활용 방안:

각 연동 지점을 MVP와 프로덕션 관점에서 나누어 설명합니다.

On-premise (또는 외부) FEPs -> NCP 데이터 수집 지점 (TainTube, TainOn)

연동 방식: 파일 전송 (SFTP/SSH) 또는 스트림 전송.
MVP:
On-prem -> NCP VM으로 SFTP/SSH를 통해 파일 직접 전송 (TainTube 대상). VM에 SSH 서버 설정 및 /data/.../rec 디렉터리 접근 권한 설정.
On-prem -> NCP VM에서 실행되는 리스너 애플리케이션으로 스트림 데이터 직접 전송 (TainOn 대상). VM 방화벽 및 ACG 설정 필요.
네트워크: 공인 인터넷망 이용. 보안을 위해 ACG에서 소스 IP 제한 필수.
프로덕션:
On-prem -> NCP Cloud Connect (VPN Gateway) 또는 전용회선을 통해 On-prem 네트워크와 NCP VPC를 안전하게 연결.
파일 전송: Cloud Connect/전용회선을 통해 NCP VPC 내 VM 또는 File Storage 서비스로 파일 전송. /data/.../rec 디렉터리는 NCP File Storage(NAS)나 Object Storage에 저장하고 VM/컨테이너에서 마운트/접근하는 방식 고려.
스트림 전송: Cloud Connect/전용회선을 통해 NCP VPC 내 TainOn 리스너로 안전하게 스트림 전송. 부하 분산을 위해 NCP Load Balancer 뒤에 TainOn 인스턴스를 여러 개 배치.
네트워크: 사설망 이용 (Cloud Connect/전용회선). ACG 및 NACL은 VPC 내에서만 적용되도록 설정.
NCP 백엔드 서비스 -> 외부 Identity Provider (IdP)

연동 방식: HTTP/HTTPS API 호출 (JWT 공개 키 JWKS 엔드포인트 접근, 토큰 검증, 사용자 정보 조회 등).
MVP / 프로덕션:
NCP 백엔드 서버(API 서버, 또는 인증 로직 포함 모듈)에서 IdP의 JWKS 엔드포인트로 아웃바운드 HTTPS (443) 요청.
네트워크: NCP VPC의 ACG 및 NACL에서 IdP의 공인 IP 대역 또는 0.0.0.0/0 (보안상 위험)에 대해 TCP 443 포트 아웃바운드 통신을 허용. 안정적인 DNS 설정 필수. IdP가 다른 클라우드에 있다면 클라우드 간 네트워크 성능 및 지연 시간 고려 (크로스 클라우드 성능 점검 필요).
IdP가 NCP 내부 다른 VPC에 있다면 VPC Peering 또는 Transit Gateway 설정 및 내부 IP 기반 ACG 규칙 설정.
외부 -> API Gateway -> NCP 백엔드 API 서비스 (Vb api svr, Vo api svr)

연동 방식: HTTP/HTTPS API 호출.
MVP:
NCP VM에 Nginx 또는 Apache 설치 후 리버스 프록시 및 로드 밸런서로 설정. 외부 트래픽을 받아 내부 NCP VPC 내의 Vb api svr, Vo api svr 인스턴스로 포워딩.
VM ACG에서 외부 IP에 대해 80/443 포트 인바운드 허용. 내부 ACG에서 VM -> API 서버 포트 인바운드 허용.
프로덕션:
NCP API Gateway Service 사용.
API Gateway 콘솔에서 외부 도메인 설정, 인증/인가 정책(API 키, JWT 기본 검증 등), Rate Limiting, 트래픽 모니터링 설정.
API Gateway 백엔드 설정을 통해 NCP VPC 내의 Vb api svr, Vo api svr 인스턴스(또는 NCP Load Balancer 뒤의 인스턴스 그룹)로 트래픽을 라우팅.
네트워크: API Gateway는 관리형 서비스이며, 백엔드 API 서버는 NCP VPC 내에 위치. API Gateway와 백엔드 API 서버 간의 통신을 허용하는 내부 ACG 규칙 설정.
NCP 백엔드 서비스 (TainTube, TainBat, TainOn, API 서버) -> NCP Cloud DB for PostgreSQL

연동 방식: 데이터베이스 클라이언트 연결 (PostgreSQL 표준 프로토콜, 기본 포트 5432).
MVP / 프로덕션:
NCP Cloud DB for PostgreSQL 인스턴스 생성. VPC Subnet 선택, 접근 제어 그룹(ACG) 설정 시 백엔드 서비스가 실행될 서브넷의 ACG를 Cloud DB ACG의 Inbound Rule에 추가.
백엔드 서비스 코드(data_access/db.py 등)에서 NCP Cloud DB 접속 정보(호스트, 포트, DB 이름, 사용자명, 비밀번호)를 사용하여 연결. 민감 정보는 환경 변수나 NCP Secrets Manager 사용.
네트워크: NCP VPC 내부 통신. 백엔드 서비스가 속한 서브넷의 ACG Outbound Rule에서 Cloud DB Subnet의 ACG Inbound Rule (포트 5432)으로의 통신을 허용.
Cloud DB 설정: MVP는 소규모 인스턴스, 단일 존 구성. 프로덕션은 고가용성(HA), 백업 설정, 주기적인 스냅샷, 필요시 읽기 전용 복제본(Read Replica) 추가.
NCP 백엔드 서비스 간 연동 (TainTube, TainBat, TainOn, API 서버)

연동 방식: 직접 함수/메소드 호출 (동일 프로세스 내), 메시지 큐 (비동기 작업 트리거), 내부 API 호출.
MVP:
간단한 함수 호출 또는 스크립트 실행 (TainBat Scheduler).
File I/O를 통한 데이터 전달 (TainTube -> /data, TainBat <- /data).
간단한 내부 API 호출 (Vo api svr -> TainBat/TainOn 트리거).
프로덕션:
메시지 큐: 비동기적이고 신뢰성 있는 구성 요소 간 통신을 위해 NCP Cloud Kafka 또는 NCP SQS (Simple Queue Service) 와 같은 메시지 큐 서비스 활용. (예: TainTube가 데이터 적재 완료 후 메시지 큐에 "새 파일 처리 완료" 메시지 발행 -> TainBat 스케줄러/러너가 메시지 수신 후 배치 시작).
내부 API: 내부 API 서버를 통해 기능을 노출하고 호출 시 NCP Internal Load Balancer 뒤의 인스턴스 그룹으로 연결.
스케줄러: 정교한 배치 스케줄링 및 워크플로우 관리를 위해 Airflow 등을 NCP VM에 구축하거나 관리형 서비스 검토.
네트워크: NCP VPC 내부 통신. ACG/NACL에서 서비스 간 통신에 필요한 포트 허용.
프론트엔드 (TainWeb) -> 백엔드 API 서비스

연동 방식: HTTP/HTTPS API 호출 (클라이언트 측 JavaScript).
MVP / 프로덕션:
권장: API Gateway URL을 통해 백엔드 API 호출. API Gateway가 CORS 처리, 인증 토큰 전달, 백엔드 라우팅 등을 담당. TainWeb은 API Gateway URL만 알면 됨.
대안 (덜 권장): 백엔드 API 서버에 직접 호출. 이 경우 백엔드 API 서버(FastAPI 등)에서 CORS (Cross-Origin Resource Sharing) 설정 필수. 보안 및 관리 복잡성 증가.
인증: TainWeb 로그인 페이지에서 Vb api svr의 /auth/token 엔드포인트 (API Gateway 경유)로 사용자 인증 정보 전송 -> 토큰 수신 -> 브라우저 스토리지(Local Storage 등)에 토큰 저장 -> 보호된 API 호출 시 Authorization: Bearer <token> 헤더에 포함하여 전송.
MVP vs. 프로덕션 완성본 차이점 요약:

기능/요소	MVP	프로덕션 완성본
On-premise -> NCP	공인망 SFTP/SSH, 직접 스트림 전송	Cloud Connect/전용회선, NAS/Object Storage 활용
API Gateway	Nginx/Apache 리버스 프록시 (VM)	NCP API Gateway Service
데이터 수집 신뢰성	파일 감지, 간단한 스트림 리스너	메시지 큐 (Kafka/SQS) 활용
데이터 저장소 (DB)	NCP Cloud DB for PostgreSQL (단일 존)	Cloud DB (HA 구성), 읽기 전용 복제본 고려
백엔드 확장성	단일 VM/컨테이너 인스턴스	NCP Auto Scaling Group, Load Balancer 활용
내부 서비스 통신	직접 호출, 파일 기반 전달	메시지 큐, Internal Load Balancer 기반 호출
스케줄링	Cron (VM 내)	Airflow (VM) 또는 관리형 스케줄링 서비스 검토
보안	ACG/NACL 기본 설정, 환경 변수	Secrets Manager, WAF, DDoS 방어 서비스 활용
모니터링/로깅	기본 로깅 (파일/콘솔)	Cloud Watch, Cloud Log Analytics 통합
정적/미디어 파일	백엔드에서 서빙 (Django static 등)	Object Storage + CDN 사용

https://docs.google.com/spreadsheets/d/1NBYFPESjayAQZlp66tB8gWeJZXqhoIa292PcAs_bHmE/edit?usp=sharing
Sheets

결론:

"swap-reporting-mvp" 프로젝트는 On-premise 데이터 수집, 클라우드 기반 처리/저장, API를 통한 서비스 제공 등 여러 분산된 구성 요소의 복합적인 연동으로 이루어집니다. NCP를 사용하면 Cloud Connect, API Gateway, Cloud DB, Load Balancer, 메시지 큐 등 다양한 관리형 서비스를 활용하여 이러한 연동을 효율적이고 안정적이며 확장 가능하게 구축할 수 있습니다.

MVP 단계에서는 기능을 빠르게 구현하기 위해 간단한 연동 방식(직접 파일 전송, 기본 리버스 프록시 등)을 사용할 수 있지만, 프로덕션 환경에서는 보안성, 가용성, 확장성을 고려하여 NCP의 관리형 서비스를 적극적으로 도입하고 자동화된 배포 및 운영 환경을 구축하는 것이 필수적입니다. 프론트엔드와 백엔드는 API Gateway를 통해 연동하는 것이 가장 표준적이고 관리 용이한 방식입니다.

=======================================================

패키징 실행:

프로젝트 루트 디렉터리에서 다음 명령어를 실행합니다.

Bash

pip install . # 로컬 환경에 패키지 설치
pip install . --target=./dist # ./dist 디렉터리에 설치 (배포용)
python setup.py sdist bdist_wheel # 소스 배포본(.tar.gz) 및 Wheel 배포본(.whl) 생성
생성된 .whl 파일은 다른 환경에서 pip install your_package_name.whl 명령으로 설치할 수 있습니다.

Docker 컨테이너를 사용한 패키징:

백엔드 서비스를 Docker 컨테이너로 패키징하는 것이 배포 및 오케스트레이션에 가장 일반적이고 권장되는 방법입니다.

swap_reporting_mvp/ui_backend/Dockerfile

Dockerfile

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

Docker 이미지 빌드:

프로젝트 루트 디렉터리에서 또는 ui_backend/ 디렉터리로 이동하여 다음 명령 실행.

Bash

# 프로젝트 루트에서 실행 시
docker build -t swap-reporting-ui-backend:latest -f ui_backend/Dockerfile .

# ui_backend/ 디렉터리로 이동하여 실행 시
# docker build -t swap-reporting-ui-backend:latest .
빌드된 이미지는 NCP Container Registry에 Push 하여 관리하고, Kubernetes Service 등에서 이 이미지를 사용하여 배포합니다.

요약:

사용자 스크린은 HTML, CSS, JavaScript로 구현하며, 백엔드 파이썬 API와 통신합니다.
이 UI를 지원하는 백엔드 파이썬 앱은 Prompt 처리 및 결과 반환 기능을 제공하는 API 서비스입니다.
이 백엔드 서비스는 setup.py를 사용하여 파이썬 패키지로 만들거나, Dockerfile을 사용하여 컨테이너 이미지로 패키징하여 배포 준비를 합니다.
Docker 컨테이너화 방식이 현대적인 클라우드 환경 배포에 더 적합하며, Kubernetes와 같은 오케스트레이션 도구를 활용하기 용이합니다.
제공해 드린 HTML 예시와 파이썬 패키징/Dockerizing 가이드를 바탕으로 여러분의 실제 UI 및 백엔드 코드에 맞춰 개발 및 패키징 작업을 진행하시면 됩니다.


=================================

ai gpu server를 포함한 repo

swap_reporting_mvp/
├── common/                 # 시스템 전반에서 공유되는 공통 코드 및 정의
│   ├── __init__.py         # Python 패키지 초기화
│   ├── data_models.py      # 데이터 모델 정의 (Pydantic 등)
│   └── utils.py            # 공통 유틸리티 함수 모음
│
├── tain_tube/              # 파일 기반 데이터 인제션 서비스
│   ├── __init__.py
│   ├── file_listener.py    # 파일 감지 및 처리 시작
│   ├── file_parser.py      # 파일 형식 파싱 로직
│   ├── data_ingestor.py    # 파싱된 데이터를 DB/Queue로 전달
│   ├── requirements.txt    # TainTube 서비스 의존성
│   └── Dockerfile          # TainTube 서비스 컨테이너화
│
├── tain_on/                # 실시간 데이터 처리 서비스
│   ├── __init__.py
│   ├── realtime_listener.py # 실시간 데이터 수신 및 전달
│   ├── tainon_processor.py  # 개별 실시간 레코드 처리 로직 (AI 추론 호출 등)
│   ├── requirements.txt    # TainOn 서비스 의존성
│   └── Dockerfile          # TainOn 서비스 컨테이너화
│
├── tain_bat/               # 배치 데이터 처리 및 스케줄링 서비스
│   ├── __init__.py
│   ├── scheduler.py        # 스케줄링 정의 및 작업 트리거
│   ├── batch_processor.py  # 대규모 배치 데이터 처리 로직 (변환, 집계 등)
│   ├── batch_anomaly_checker.py # 배치 이상 탐지 실행 로직
│   ├── requirements.txt    # TainBat 서비스 의존성
│   └── Dockerfile          # TainBat 서비스 컨테이너화
│
├── ui_backend/             # 사용자 인터페이스(TainWeb) 백엔드 API 서비스
│   ├── __init__.py
│   ├── api.py              # FastAPI 앱 정의 및 API 엔드포인트
│   ├── processing.py       # UI 요청 처리 비즈니스 로직 (다른 서비스 호출)
│   ├── requirements.txt    # UI 백엔드 서비스 의존성
│   └── Dockerfile          # UI 백엔드 서비스 컨테이너화
│
├── ai_inference_service/   # AI 모델 추론 전용 서비스 (GPU 활용)
│   ├── __init__.py
│   ├── inference_api.py    # 추론 요청 수신 API (gRPC 또는 REST)
│   ├── model_loader.py     # 모델 로딩 및 관리
│   ├── model_predictor.py  # 실제 추론 실행 로직 (GPU 라이브러리 사용)
│   ├── requirements.txt    # AI Inference 서비스 의존성 (GPU 관련 포함)
│   └── Dockerfile          # AI Inference 서비스 컨테이너화
│
├── ml_training_service/    # AI 모델 학습 전용 서비스 (GPU 활용)
│   ├── __init__.py
│   ├── training_workflow.py # 학습 워크플로우 정의 (Scheduler에 의해 트리거)
│   ├── data_sampler.py     # DB 등에서 학습 데이터 샘플링
│   ├── model_trainer.py    # 실제 모델 학습 로직 (다양한 모델, GPU 라이브러리 사용)
│   ├── model_evaluator.py  # 모델 평가 및 비교
│   ├── model_saver.py      # 학습된 모델 저장소에 저장
│   ├── requirements.txt    # ML Training 서비스 의존성 (GPU 관련, ML 프레임워크 포함)
│   └── Dockerfile          # ML Training 서비스 컨테이너화
│
├── reporting_service/      # 보고서 생성 및 전송 서비스
│   ├── __init__.py
│   ├── report_generator.py # 다양한 보고서 형식 생성 로직 (KTFC, 누적 등)
│   ├── report_transmitter.py # 생성된 보고서를 외부 시스템(KTFC/SDR)으로 전송
│   ├── requirements.txt    # Reporting 서비스 의존성
│   └── Dockerfile          # Reporting 서비스 컨테이너화
│
├── alerting_service/       # 시스템 알림 발송 서비스
│   ├── __init__.py
│   ├── alert_manager.py    # 알림 규칙 관리
│   ├── notification_sender.py # 이메일, 메신저 등 실제 알림 발송 로직
│   ├── requirements.txt    # Alerting 서비스 의존성
│   └── Dockerfile          # Alerting 서비스 컨테이너화
│
├── tests/                  # 시스템 테스트 코드 모음
│   ├── unit/               # 단위 테스트
│   │   └── test_utils.py
│   ├── integration/        # 통합 테스트 (서비스 간 연동, Mocking 등)
│   │   └── test_ui_backend_integration.py
│   └── performance/        # 성능 테스트 (부하 테스트 등)
│       └── test_ui_backend_performance.py
│
├── docs/                   # 프로젝트 문서 (설계 문서, 사용자 가이드 등)
│   ├── architecture.md
│   ├── data_model.md
│   └── ...
│
├── deployment/             # 배포 관련 설정 파일 (Kubernetes YAML, Docker Compose 등)
│   ├── kubernetes/
│   │   ├── tain_on.yaml
│   │   ├── ui_backend.yaml
│   │   ├── ai_inference.yaml
│   │   └── ...
│   ├── docker-compose.yaml # 개발/테스트 환경용
│   └── ...
│
├── scripts/                # 유용한 스크립트 (빌드, 배포, DB 초기화 등)
│   ├── build_images.sh
│   ├── deploy.sh
│   └── ...
│
├── README.md               # 프로젝트 개요 및 설정 방법
├── requirements.txt        # 개발 환경 설정 또는 전체 프로젝트 공통 의존성
└── .gitignore              # Git 버전 관리에서 제외할 파일/디렉터리 지정
