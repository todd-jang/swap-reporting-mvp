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
