swap_reporting_mvp/
├── ui_backend/            # UI 백엔드 서비스 코드 디렉터리
│   ├── __init__.py        # 파이썬 패키지 초기화 파일
│   ├── api.py             # FastAPI/Flask 앱 객체 및 API 엔드포인트 정의
│   ├── processing.py      # UI 요청에 따른 데이터 처리 및 다른 서비스 호출 로직
│   ├── requirements.txt   # 이 서비스만의 파이썬 의존성 목록
│   ├── Dockerfile         # 이 서비스의 도커 이미지 빌드 파일 (컨테이너화 시)
│   └── ... (UI 백엔드 관련 다른 파일들)
│
├── tain_tube/             # TainTube 서비스 코드 디렉터리
│   ├── ...
│
├── tain_bat/              # TainBat 서비스 코드 디렉터리
│   ├── scheduler.py       # 스케줄러 로직
│   ├── ...
│
├── tain_on/               # TainOn 서비스 코드 디렉터리
│   ├── realtime_listener.py # 실시간 리스너 로직
│   ├── tainon_processor.py  # 실시간 처리 로직
│   └── ...
│
├── common/                # 공통 유틸리티, 데이터 모델 정의 등
│   ├── utils.py
│   ├── data_models.py
│   └── ...
│
├── docs/                  # 문서
├── tests/                 # 테스트 코드
├── README.md              # 프로젝트 설명 파일
├── requirements.txt       # 전체 프로젝트 공통 또는 개발 환경 의존성 (선택 사항)
└── ... (프로젝트 관련 기타 파일)

재정의된 파일들의 연동:

realtime_listener.py는 외부로부터 실시간 데이터를 수신합니다.
수신된 데이터 레코드를 tainon_processor.py의 process_realtime_swap_data 함수로 전달합니다.
tainon_processor.py는 전달받은 데이터를 전처리하고, 미리 로딩해 둔 AI 모델(deployed_ensemble_model)을 사용하여 이상치 추론을 수행합니다.
이상치 추론 결과와 현재 시간 조건을 확인하여, 필요시 reporting_service(개념적인 별도 서비스)의 함수(trigger_immediate_anomaly_alert, generate_immediate_anomaly_report)를 호출하여 Alert 및 보고서 생성을 트리거하거나, 정상 데이터 처리 함수를 호출합니다.
scheduler.py는 정해진 스케줄에 따라 tainon_processor.py를 직접 호출하지는 않지만, 별도의 AI 학습 서비스나 TainBat의 배치 이상 탐지 함수(trigger_batch_anomaly_check_job), 보고서 생성 서비스 함수(trigger_daily_ktfc_report_if_weekday 등)를 호출하여 전체 워크플로우를 조율합니다.
이러한 방식으로 각 파일은 자신의 명확한 역할(스케줄링, 수신, 실시간 처리)을 수행하며, 함수 호출을 통해 다른 컴포넌트와 상호 작용하여 복잡한 스왑 데이터 보고 워크플로우를 실현합니다.

=====================

실행 방법 (개발 환경):

위 4개의 파일을 적절한 디렉터리 구조(swap_reporting_mvp/common/, swap_reporting_mvp/ui_backend/)에 저장합니다.
필요한 라이브러리 설치: pip install fastapi uvicorn pydantic numpy scikit-learn requests (requests는 다른 서비스 호출 시 필요, numpy/sklearn은 utils 예시 및 가상 데이터에 사용)
ui_backend/api.py 파일의 맨 아래 if __name__ == "__main__": 블록의 주석을 해제합니다.
프로젝트 루트 디렉터리(swap_reporting_mvp) 또는 ui_backend 디렉터리에서 PYTHONPATH를 설정하거나, uvicorn ui_backend.api:app --reload 명령을 실행합니다 (import 오류 해결 필요).
브라우저에서 http://127.0.0.1:8000/docs 또는 http://localhost:8000/docs 에 접속하여 FastAPI Swagger UI를 통해 API를 테스트할 수 있습니다.

--------------------

테스트 실행:

pytest 명령어를 사용하여 실행합니다. tests/unit 디렉터리에서 실행하거나 프로젝트 루트에서 실행할 수 있습니다.

```Bash

pytest tests/unit/
# 또는 프로젝트 루트에서
# pytest tests/unit/test_utils.py

pytest tests/integration/
