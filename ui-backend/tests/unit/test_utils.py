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
