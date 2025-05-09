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
