1. 데이터 수집 및 적재 연동:

Vb fep 및 /data/yyyymmdd/rec: Vb fep (Front-End Processor)는 외부 소스로부터 스왑 데이터를 수신하여 특정 디렉터리 구조(/data/yyyymmdd/rec)의 파일 형태로 저장하는 역할을 합니다. 이는 배치(Batch)성 데이터 입력의 시작점입니다.
/data/yyyymmdd/rec -> TainTube: TainTube 구성 요소는 /data/.../rec 디렉터리에 저장된 파일들을 주기적으로 감지하거나 특정 이벤트에 의해 트리거되어 읽어옵니다. 이것이 TainTube의 주요 입력 경로입니다.
Vo fep -> stream -> TainOn: Vo fep는 다른 외부 소스로부터 스왑 데이터를 실시간 또는 스트림(Stream) 형태로 수신합니다. 이 스트림 데이터는 직접 TainOn 구성 요소로 전달됩니다. 이것이 TainOn의 주요 입력 경로이며, 실시간(Real-time) 또는 준실시간 데이터 처리를 위한 연동입니다.
TainTube -> DB (TB_BAT_FILE_MST, TB_BAT_FILE_HIST): TainTube는 읽어온 입력 파일의 데이터를 파싱하고 유효성을 검증한 후, 원본 데이터 또는 초기 검증된 데이터를 데이터베이스(예: TB_BAT_FILE_MST - 마스터 파일 기록, TB_BAT_FILE_HIST - 기록/로그)에 적재합니다. 파일 기반 입력 데이터의 1차 저장소 연동입니다.
TainOn -> DB (TB_ON_MST, TB_ON_HIST): TainOn은 수신한 실시간 스트림 데이터를 처리하고 필요한 변환/검증을 수행한 후, 처리된 데이터를 데이터베이스(예: TB_ON_MST - 온라인 마스터 테이블, TB_ON_HIST - 기록/로그)에 적재합니다. 실시간 입력 데이터의 저장소 연동입니다.
2. 데이터 처리 및 보고서 생성 연동:

DB (TB_BAT_FILE_MST 등) -> TainBat: TainBat (배치 처리) 구성 요소는 주기적으로 (예: 일별) 데이터베이스에 적재된 원본 데이터 또는 초기 처리된 데이터를 읽어옵니다.
TainBat -> DB (TB_ON_MST, TB_ON_HIST) 및 /data/yyyymmdd/send: TainBat는 읽어온 데이터를 CFTC 가이드라인에 따라 복잡한 변환, 집계, 연산 등을 수행한 후, 처리된/집계된 최종 데이터를 데이터베이스(예: TB_ON_MST, TB_ON_HIST)에 저장합니다. 또한, CFTC 보고서 형식에 맞는 최종 보고서 파일이나 전송할 데이터를 /data/.../send 디렉터리에 생성합니다. 이것이 TainBat의 주요 출력 연동입니다.
TainOn -> DB (TB_ON_MST, TB_ON_HIST): TainOn은 실시간 데이터 처리 후 결과를 DB에 저장할 뿐만 아니라, 온디맨드(On-demand) 보고서 요청이 들어오면 데이터베이스에 저장된 데이터를 읽어와 보고서를 생성하는 데 활용합니다.
3. API 서비스를 통한 접근 및 제어 연동:

외부 / TainWeb -> api -> Vb api svr / Vo api svr: 외부 사용자나 웹 UI (TainWeb)는 API Gateway 또는 직접 Vb api svr 및 Vo api svr와 HTTP/HTTPS 프로토콜 기반의 API 호출을 통해 상호작용합니다. 이것이 시스템 기능에 접근하는 주요 통로입니다.
api -> jwt -> Vb api svr / Vo api svr: Vb api svr와 Vo api svr는 수신된 API 요청에 대해 jwt (JSON Web Token) 기반의 인증 및 권한 부여를 수행합니다. 클라이언트가 제공한 토큰의 유효성을 검증하고 사용자의 접근 권한을 확인합니다.
Vb api svr -> DB: Vb api svr는 인증/권한 부여된 요청에 따라 데이터베이스에서 필요한 데이터를 조회하고 클라이언트에게 응답합니다 (예: 특정 스왑 데이터 조회).
Vo api svr -> DB: Vo api svr는 보고서 상태 조회와 같은 요청에 대해 데이터베이스에서 정보를 조회합니다.
Vo api svr -> TainBat / TainOn: Vo api svr는 사용자 요청(예: 보고서 생성 요청)에 따라 TainBat (배치) 또는 TainOn (온디맨드 보고서 생성) 구성 요소의 특정 기능을 트리거하는 역할을 할 수 있습니다. API 호출이 백그라운드 작업(배치)을 시작시키는 연동입니다.
/data/yyyymmdd/send -> Vo fep -> stream: TainBat가 생성한 보고서 파일은 /data/.../send 디렉터리에 저장됩니다. Vo fep는 이 파일을 읽어와 외부 시스템으로 스트림 형태로 전송하는 역할을 할 수 있습니다. 이것은 처리된 데이터를 외부로 다시 내보내는 (Outgestion) 연동입니다.
Vo api svr <- /data/yyyymmdd/send (추정): 다이어그램에 명시적 화살표는 없지만, Vo api svr가 생성된 보고서 파일을 다운로드하는 기능을 제공한다면 /data/.../send 디렉터리에서 파일을 읽어오는 연동이 있을 수 있습니다.
요약:

이 아키텍처는 크게 데이터 수집/적재(Ingestion), 데이터 처리(Processing), **데이터 제공/제어(Serving/Control)**의 세 가지 주요 흐름을 가집니다.

데이터는 파일 또는 스트림 형태로 Vb fep / Vo fep를 통해 시스템에 진입합니다.
TainTube와 TainOn은 각각 파일 및 스트림 형태의 데이터를 초기 처리하고 데이터베이스에 적재합니다.
TainBat는 주기적으로 DB의 데이터를 읽어 복잡한 배치 처리를 수행하고 결과를 다시 DB나 파일로 저장합니다.
Vb api svr 및 Vo api svr는 인증을 거쳐 데이터를 조회하거나 보고서 생성과 같은 백그라운드 작업을 제어하는 API 인터페이스를 제공합니다.
처리된 보고서 파일은 Vo fep를 통해 외부로 전송될 수 있습니다.
이 모든 과정은 데이터베이스와 파일 시스템을 중심으로 데이터를 공유하고 상태를 관리하며 연동됩니다.
