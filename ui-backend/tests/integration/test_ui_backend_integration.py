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
