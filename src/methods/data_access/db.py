# swap_reporting_mvp/data_access/db.py

# 이 파일은 가상 데이터베이스 상호작용 함수를 정의합니다.
# 실제 프로젝트에서는 SQLAlchemy, Django ORM, MyBATIS 등 사용
import datetime

# 가상 데이터 저장소 (실제 DB 아님)
_raw_cftc_records = []
_aggregated_cftc_data = {}
_report_status = {}

def save_raw_cftc_record(record):
    """가상 원본 CFTC 레코드 저장."""
    print(f"DB: 원본 레코드 저장 시도 - {record.get('UNIQUE_ID')}")
    _raw_cftc_records.append(record)
    print("DB: 원본 레코드 저장 완료")

def get_raw_data_for_batch(process_date: datetime.date):
    """가상 배치 처리를 위한 원본 데이터 조회."""
    print(f"DB: 배치 처리를 위한 원본 데이터 조회 시도 - 날짜: {process_date}")
    # 실제 DB에서는 날짜 기준으로 필터링
    data = [r for r in _raw_cftc_records if r.get('TRADE_DATE') == process_date]
    print(f"DB: 원본 데이터 {len(data)}개 조회 완료")
    return data

def save_aggregated_data(aggregated_data_list):
    """가상 집계 데이터 저장."""
    print(f"DB: 집계 데이터 저장 시도 - {len(aggregated_data_list)}개")
    for item in aggregated_data_list:
         # 가상 저장 로직 (예: 기준별 덮어쓰기)
         key = tuple(item.get(c) for c in item.get('GroupCriteria', [])) # GroupCriteria는 테스트 코드에서 임시 추가
         _aggregated_cftc_data[key] = item
    print("DB: 집계 데이터 저장 완료")

def get_processed_data_for_report(report_criteria):
    """가상 보고서 생성을 위한 처리/집계 데이터 조회."""
    print(f"DB: 보고서 데이터 조회 시도 - 기준: {report_criteria}")
    # 실제 DB에서는 기준에 따라 쿼리
    data = list(_aggregated_cftc_data.values())
    print(f"DB: 보고서 데이터 {len(data)}개 조회 완료")
    return data

def update_report_status(report_id, status, completion_time=None):
    """가상 보고서 상태 업데이트."""
    print(f"DB: 보고서 상태 업데이트 - ID: {report_id}, 상태: {status}")
    _report_status[report_id] = {"status": status, "completion_time": completion_time}
    print("DB: 보고서 상태 업데이트 완료")

def get_report_status_by_id(report_id):
    """가상 보고서 상태 조회."""
    print(f"DB: 보고서 상태 조회 - ID: {report_id}")
    return _report_status.get(report_id)

# TODO: 다른 필요한 DB 상호작용 함수 추가 (예: 사용자 정보 조회, 파일 처리 상태 기록 등)
