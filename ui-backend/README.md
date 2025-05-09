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

코딩 파트너

생각하는 과정 표시
네, tests 디렉터리에 단위 테스트, UI 백엔드 통합 시뮬레이션 테스트, 통합 성능 테스트 예시 코드를 작성해 보겠습니다.

테스트는 애플리케이션의 품질을 보장하고 변경 사항이 기존 기능을 손상시키지 않음을 확인하는 데 필수적입니다. Python에서 널리 사용되는 pytest 프레임워크를 기반으로 예시를 작성하겠습니다.

프로젝트 구조:

swap_reporting_mvp/
├── common/
│   ├── data_models.py
│   └── utils.py
├── ui_backend/
│   ├── api.py
│   └── processing.py
└── tests/
    ├── unit/               # 단위 테스트
    │   └── test_utils.py
    ├── integration/        # 통합 시뮬레이션 테스트 (다른 서비스 Mocking)
    │   └── test_ui_backend_integration.py
    ├── performance/        # 통합 성능 테스트 예시
    │   └── test_ui_backend_performance.py
    └── __init__.py         # 테스트 디렉터리임을 알리는 빈 파일
필요 라이브러리 설치:

Bash

pip install pytest pytest-mock httpx # httpx는 FastAPI 테스트 클라이언트용
1. 단위 테스트 (tests/unit/test_utils.py)

common/utils.py와 같은 개별 함수나 모듈의 특정 기능이 예상대로 작동하는지 독립적으로 테스트합니다.

Python

# tests/unit/test_utils.py

import datetime
import pytest
from common import utils # common 디렉터리의 utils 모듈 임포트

# is_weekday 함수 단위 테스트
def test_is_weekday():
    # 월요일부터 금요일은 True
    assert utils.is_weekday(datetime.date(2023, 10, 23)) is True  # 월요일
    assert utils.is_weekday(datetime.date(2023, 10, 27)) is True  # 금요일
    # 토요일, 일요일은 False
    assert utils.is_weekday(datetime.date(2023, 10, 28)) is False # 토요일
    assert utils.is_weekday(datetime.date(2023, 10, 29)) is False # 일요일

# is_holiday 함수 단위 테스트 (가상 공휴일 기준)
# 실제 구현 시에는 공휴일 데이터 의존성을 Mocking 해야 합니다.
def test_is_holiday():
    # 가상 공휴일 (1월 1일)
    assert utils.is_holiday(datetime.date(2024, 1, 1)) is True
    assert utils.is_holiday(datetime.date(2024, 1, 2)) is False
    assert utils.is_holiday(datetime.date(2023, 12, 25)) is False # 가상 공휴일 아님

# is_business_hours 함수 단위 테스트 (가상 공휴일 및 시간 기준)
def test_is_business_hours():
    # 주중 업무 시간 내 (화요일 10:30)
    assert utils.is_business_hours(datetime.datetime(2023, 10, 24, 10, 30)) is True
    # 주중 업무 시간 경계 (목요일 09:00)
    assert utils.is_business_hours(datetime.datetime(2023, 10, 26, 9, 0)) is True
     # 주중 업무 시간 경계 (수요일 14:59:59)
    assert utils.is_business_hours(datetime.datetime(2023, 10, 25, 14, 59, 59)) is True
    # 주중 업무 시간 외 (금요일 08:59)
    assert utils.is_business_hours(datetime.datetime(2023, 10, 27, 8, 59)) is False
    # 주중 업무 시간 외 (월요일 15:00)
    assert utils.is_business_hours(datetime.datetime(2023, 10, 23, 15, 0)) is False
    # 주말 업무 시간 내 시간 (토요일 11:00)
    assert utils.is_business_hours(datetime.datetime(2023, 10, 28, 11, 0)) is False
    # 공휴일 업무 시간 내 시간 (가상 공휴일 1월 1일 10:00)
    assert utils.is_business_hours(datetime.datetime(2024, 1, 1, 10, 0)) is False


# generate_unique_id 함수 단위 테스트
def test_generate_unique_id():
    id1 = utils.generate_unique_id()
    id2 = utils.generate_unique_id()
    # 고유 ID는 서로 달라야 함
    assert id1 != id2
    # UUID 형식인지 기본적인 검증 (optional)
    assert isinstance(id1, str)
    assert len(id1) > 0 # 더 엄격한 UUID 형식 검증 라이브러리 사용 가능

# TODO: 다른 유틸리티 함수들에 대한 단위 테스트 추가 (format_cftc_date 등)
# TODO: 데이터 모델 (data_models.py)에 복잡한 validation 로직이 있다면 해당 로직에 대한 단위 테스트 추가
테스트 실행:

pytest 명령어를 사용하여 실행합니다. tests/unit 디렉터리에서 실행하거나 프로젝트 루트에서 실행할 수 있습니다.

Bash

pytest tests/unit/
# 또는 프로젝트 루트에서
# pytest tests/unit/test_utils.py
2. 통합 시뮬레이션 테스트 (tests/integration/test_ui_backend_integration.py)

UI 백엔드(api.py, processing.py)가 의존하는 다른 서비스(AI 모델, DB 매니저, 보고서 서비스 등)와의 **상호작용을 Mocking(가짜 객체로 대체)**하여 테스트합니다. 실제 외부 서비스 호출 없이, UI 백엔드 로직이 예상대로 다른 컴포넌트의 함수/메소드를 호출하고 응답을 처리하는지 확인합니다.

Python

# tests/integration/test_ui_backend_integration.py

from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock # Mocking을 위해
import json # JSON 데이터 처리를 위해

# 테스트할 FastAPI 애플리케이션 임포트
from ui_backend.api import app

# TestClient 생성 (FastAPI 애플리케이션을 테스트 가능하게 함)
client = TestClient(app)

# Mock 대상 모듈 경로 정의 (ui_backend/processing.py에서 임포트하는 외부 의존성)
# 실제 사용하는 모듈 경로에 맞게 수정해야 합니다.
# 예: processing.py 에서 common.db_manager 를 import 한다면, 'common.db_manager' 로 지정
MOCK_DB_MANAGER_PATH = 'ui_backend.processing.db_manager' # common.db_manager 가 ui_backend.processing 에 의해 호출된다고 가정
MOCK_REPORTING_SERVICE_PATH = 'ui_backend.processing.reporting_service'
MOCK_AI_UTIL_PATH = 'common.utils.predict_anomaly_with_ensemble_model' # common.utils 에 정의된 AI 예측 함수가 호출된다고 가정
MOCK_CACHE_FUNCTION_PATH = 'ui_backend.processing.cache_result' # 캐시 저장 함수 경로


# /process_prompt 엔드포인트 테스트 (이상 거래 조회 프롬프트 시뮬레이션)
# patch 데코레이터를 사용하여 의존성 Mocking
@patch(MOCK_DB_MANAGER_PATH)
@patch(MOCK_CACHE_FUNCTION_PATH)
def test_process_prompt_anomaly_query(mock_cache_result, mock_db_manager):
    # Mock 객체의 반환값 설정: DB에서 특정 레코드를 조회한 것처럼 시뮬레이션
    # common.data_models 의 SwapRecord 객체 사용
    from common.data_models import SwapRecord
    mock_records = [
        SwapRecord(unique_transaction_identifier='UTI_TEST_001', reporting_counterparty_lei='LEI1', other_counterparty_lei='LEI2',
                   asset_class='IR', swap_type='IRS', action_type='NEWT', execution_timestamp=datetime.datetime.utcnow(),
                   effective_date=datetime.date.today(), expiration_date=datetime.date.today(), notional_currency_1='USD', notional_value_1=1e6,
                   ai_prediction_label='이상치', ai_anomaly_score=-0.8),
         SwapRecord(unique_transaction_identifier='UTI_TEST_002', reporting_counterparty_lei='LEI3', other_counterparty_lei='LEI4',
                   asset_class='FX', swap_type='CCS', action_type='NEWT', execution_timestamp=datetime.datetime.utcnow(),
                   effective_date=datetime.date.today(), expiration_date=datetime.date.today(), notional_currency_1='EUR', notional_value_1=5e5,
                   ai_prediction_label='이상치', ai_anomaly_score=-0.9),
    ]
    # mock_db_manager 객체의 특정 메소드(예: get_recent_anomalous_records)의 반환값 설정
    # mock_db_manager.get_recent_anomalous_records.return_value = mock_records

    # 가상 데이터 사용 시에는 Mocking 불필요 (processing.py 내부에서 가상 데이터를 사용하므로)
    # 만약 processing.py가 실제 DB 함수를 호출한다면 Mocking 필요.
    # 여기서는 processing.py의 가상 데이터 로직을 테스트하는 셈이므로 Mocking 안 함.

    # API 엔드포인트 호출
    response = client.post("/process_prompt", json={"prompt": "최근 이상 거래 레코드 조회해 줘"})

    # 응답 상태 코드 확인
    assert response.status_code == 200

    # 응답 데이터 확인 (common.data_models 의 ProcessPromptResponse 형식)
    response_data = response.json()
    assert response_data['status'] == "Success"
    assert "총 2 건의 잠재적 이상 거래가 탐지되었습니다." in response_data['text_result'] # 가상 데이터 기준 예상 결과
    assert len(response_data['related_record_ids']) > 0

    # Mocking된 캐시 함수가 호출되었는지 확인
    # mock_cache_result.assert_called_once() # 가상 데이터 사용 시 내부 함수 호출 Mocking 필요

# /cached_results 엔드포인트 테스트
@patch(MOCK_DB_MANAGER_PATH)
def test_get_cached_results(mock_db_manager):
    # Mock 객체의 반환값 설정: DB에서 캐시된 결과를 조회한 것처럼 시뮬레이션
    from common.data_models import CachedResult
    mock_cached_list = [
        CachedResult(id='cache_1', prompt='Prompt A', text_summary='Summary A', timestamp=datetime.datetime.utcnow() - datetime.timedelta(minutes=1)),
        CachedResult(id='cache_2', prompt='Prompt B', text_summary='Summary B', timestamp=datetime.datetime.utcnow()),
    ]
    # mock_db_manager.get_recent_cached_results.return_value = mock_cached_list

    # 가상 데이터 사용 시 Mocking 불필요

    # API 엔드포인트 호출
    response = client.get("/cached_results", params={"limit": 5})

    # 응답 상태 코드 확인
    assert response.status_code == 200

    # 응답 데이터 확인 (common.data_models 의 CachedResult 목록 형식)
    cached_results = response.json()
    assert isinstance(cached_results, list)
    # assert len(cached_results) == 2 # 가상 데이터 사용 시 결과 개수 확인

    # TODO: 다른 Prompt 시뮬레이션 테스트 추가 (예: 레코드 상세 조회, 보고서 생성 요청 등)
    # TODO: 오류 발생 시 (예: DB 연결 실패) API가 올바른 오류 응답을 반환하는지 테스트
테스트 실행:

Bash

pytest tests/integration/
3. 통합 성능 테스트 (tests/performance/test_ui_backend_performance.py)

UI 백엔드 엔드포인트(process_prompt, cached_results)가 높은 부하 조건에서 얼마나 빠르게 응답하는지, 초당 몇 건의 요청을 처리할 수 있는지 등을 측정합니다. 이는 실제 부하 테스트 도구(Locust, Artillery 등)를 사용하는 것이 이상적이지만, 여기서는 Python의 requests 및 concurrent.futures를 사용하여 개념적인 동시 요청 및 응답 시간 측정 예시를 보여줍니다.

이 코드는 실제 부하 테스트 도구보다 기능이 매우 제한적입니다.

Python

# tests/performance/test_ui_backend_performance.py

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest # pytest 사용 시 테스트 함수로 정의

# 테스트 대상 API URL (로컬에서 실행 시)
API_URL = "http://127.0.0.1:8000"

# 성능 테스트 설정
NUM_CONCURRENT_USERS = 10 # 동시에 요청을 보낼 스레드 수
NUM_REQUESTS_PER_USER = 50 # 각 스레드가 보낼 요청 수
TEST_PROMPT = "최근 이상 거래 조회" # 테스트에 사용할 Prompt

def send_prompt_request(prompt: str):
    """Prompt 처리 요청을 보내고 응답 시간을 측정하는 함수."""
    start_time = time.time()
    try:
        response = requests.post(f"{API_URL}/process_prompt", json={"prompt": prompt}, timeout=10) # 10초 타임아웃
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생
        end_time = time.time()
        return (end_time - start_time, response.status_code, None) # 응답 시간, 상태 코드, 오류 없음
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        return (end_time - start_time, None, e) # 응답 시간, 상태 코드 (없음), 오류

def send_cached_results_request(limit: int):
    """캐시 결과 조회 요청을 보내고 응답 시간을 측정하는 함수."""
    start_time = time.time()
    try:
        response = requests.get(f"{API_URL}/cached_results", params={"limit": limit}, timeout=10)
        response.raise_for_status()
        end_time = time.time()
        return (end_time - start_time, response.status_code, None)
    except requests.exceptions.RequestException as e:
        end_time = time.time()
        return (end_time - start_time, None, e)


# pytest 테스트 함수로 정의
# @pytest.mark.skip(reason="성능 테스트는 별도로 실행") # 필요시 주석 해제하여 pytest 실행에서 제외
def test_process_prompt_performance():
    print(f"\n--- 성능 테스트 시작: /process_prompt ({NUM_CONCURRENT_USERS} 사용자, 각 {NUM_REQUESTS_PER_USER} 요청) ---")

    request_times = []
    successful_requests = 0
    failed_requests = 0

    # ThreadPoolExecutor를 사용하여 동시 요청 시뮬레이션
    with ThreadPoolExecutor(max_workers=NUM_CONCURRENT_USERS) as executor:
        # 모든 요청을 제출
        future_to_request = {
            executor.submit(send_prompt_request, TEST_PROMPT): i
            for i in range(NUM_CONCURRENT_USERS * NUM_REQUESTS_PER_USER)
        }

        # 요청 완료를 기다리고 결과 처리
        for future in as_completed(future_to_request):
            request_index = future_to_request[future]
            try:
                elapsed_time, status_code, error = future.result()
                if error:
                    failed_requests += 1
                    print(f"  요청 {request_index} 실패: {error}")
                else:
                    successful_requests += 1
                    request_times.append(elapsed_time)
                    # print(f"  요청 {request_index} 완료: {elapsed_time:.4f} 초 (상태: {status_code})")
            except Exception as exc:
                failed_requests += 1
                print(f"  요청 {request_index} 처리 중 예외 발생: {exc}")

    print("\n--- 성능 테스트 결과 ---")
    total_requests = NUM_CONCURRENT_USERS * NUM_REQUESTS_PER_USER
    print(f"총 요청 수: {total_requests}")
    print(f"성공 요청 수: {successful_requests}")
    print(f"실패 요청 수: {failed_requests}")
    if successful_requests > 0:
        print(f"평균 응답 시간: {sum(request_times) / successful_requests:.4f} 초")
        print(f"최소 응답 시간: {min(request_times):.4f} 초")
        print(f"최대 응답 시간: {max(request_times):.4f} 초")
        # 중앙값, 90분위수 등 추가 통계 계산 가능
        # 초당 처리량 (요청/초) 계산: 성공 요청 수 / (전체 테스트 시간) - 실제 부하 도구가 더 정확
        # 대략적인 처리량: total_requests / max(request_times) if max(request_times) > 0 else 0
    else:
        print("성공한 요청이 없어 통계 계산 불가.")

    assert failed_requests == 0 # 모든 요청이 성공했는지 확인 (엄격한 기준)
    assert successful_requests == total_requests


# TODO: /cached_results 엔드포인트에 대한 성능 테스트 함수 추가
# def test_cached_results_performance():
#    # 유사한 방식으로 구현
#    pass

# 이 파일을 직접 실행하여 테스트할 수도 있습니다 (pytest 없이).
# if __name__ == "__main__":
#     # FastAPI 애플리케이션을 별도의 터미널에서 먼저 실행해야 합니다.
#     # uvicorn ui_backend.api:app --reload
#     test_process_prompt_performance()

===================================================

테스트 실행 (성능):

ui_backend/api.py 파일을 별도의 터미널에서 실행합니다.
Bash

uvicorn ui_backend.api:app --reload
다른 터미널에서 tests/performance/ 디렉터리로 이동하여 pytest를 실행합니다.
Bash

pytest tests/performance/test_ui_backend_performance.py
또는 pytest 실행 시 --skip 옵션을 사용했다면 해당 부분을 제거하거나, 직접 파일 맨 아래 if __name__ == "__main__": 블록 주석을 해제하고 실행합니다.
각 테스트의 목적:

단위 테스트: 가장 작고 독립적인 코드 조각이 정확한 기능을 하는지 빠르게 확인합니다. 개발 단계에서 버그를 조기에 발견하는 데 유용합니다.
통합 시뮬레이션 테스트: 여러 컴포넌트(여기서는 UI 백엔드와 Mocking된 외부 서비스)가 서로 올바르게 상호작용하는지 확인합니다. 실제 외부 서비스 없이 통합 로직을 검증할 때 유용합니다.
통합 성능 테스트: 시스템(또는 특정 부분)이 예상되는 부하 조건에서 얼마나 잘 작동하는지, 응답 시간이나 처리량 요구사항을 만족하는지 측정합니다. 시스템의 확장성 및 병목 지점 파악에 중요합니다.
제공된 코드 예시는 각 테스트 유형의 기본 구조와 개념을 보여줍니다. 실제 프로젝트의 복잡성에 맞춰 테스트 케이스를 더 상세하게 작성하고, Mocking 대상 및 성능 테스트 시나리오를 구체화해야 합니다.
