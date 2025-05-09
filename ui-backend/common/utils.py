# common/utils.py

import datetime
import uuid # 고유 ID 생성을 위해
import random # 예시용 랜덤 데이터 생성에 사용

def is_weekday(date_obj: datetime.date) -> bool:
    """
    주어진 날짜가 주중(월~금)인지 확인합니다.
    """
    return date_obj.weekday() < 5

def is_holiday(date_obj: datetime.date) -> bool:
    """
    주어진 날짜가 공휴일인지 확인합니다.
    TODO: 실제 구현 시 공휴일 데이터베이스 또는 API를 사용해야 합니다.
    """
    # 가상 공휴일 예시 (매년 1월 1일)
    if date_obj.month == 1 and date_obj.day == 1:
        return True
    # 실제 구현 필요
    return False

def is_business_hours(datetime_obj: datetime.datetime) -> bool:
    """
    주어진 타임스탬프가 업무 시간(09:00 ~ 15:00) 중 주중/비공휴일인지 확인합니다.
    """
    if not is_weekday(datetime_obj.date()) or is_holiday(datetime_obj.date()):
        return False
    hour = datetime_obj.hour
    minute = datetime_obj.minute
    # 09:00 <= time < 15:00
    if 9 <= hour < 15:
        return True
    # 15:00 정각은 제외
    # if hour == 15 and minute == 0:
    #     return False
    return False


def generate_unique_id() -> str:
    """
    시스템 내에서 사용될 고유 ID를 생성합니다 (UUID 기반).
    """
    return str(uuid.uuid4())

def generate_report_id(report_type: str) -> str:
    """
    보고서 타입 기반 고유 보고서 ID를 생성합니다.
    """
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{report_type}_{timestamp_str}_{uuid.uuid4().hex[:8]}"

def format_cftc_date(date_obj: datetime.date) -> str:
    """
    CFTC 보고 규격에 맞는 날짜 형식(YYYY-MM-DD)으로 변환합니다.
    """
    return date_obj.strftime("%Y-%m-%d")

def format_cftc_datetime(datetime_obj: datetime.datetime) -> str:
    """
    CFTC 보고 규격에 맞는 타임스탬프 형식으로 변환합니다.
    TODO: 실제 CFTC 규격에 따라 초, 밀리초 등 정밀도 조정 필요. UTC 기준.
    """
    return datetime_obj.strftime("%Y-%m-%dT%H:%M:%S.%fZ") # ISO 8601 형식 예시


# --- 데이터 전처리 및 특징 추출 관련 유틸리티 (개념적) ---

def preprocess_for_inference(swap_record: dict) -> np.ndarray:
    """
    단일 스왑 레코드 딕셔너리에서 AI 모델 추론을 위한 특징 벡터 (NumPy 배열)를 추출하고 전처리합니다.
    TODO: 실제 스왑 레코드 필드를 기반으로 특징 추출 및 스케일링 로직 구현
    """
    # 예시: 'notional_value_1'과 'price' 필드를 특징으로 사용한다고 가정
    feature1 = swap_record.get('notional_value_1', 0.0)
    feature2 = swap_record.get('price', 0.0)
    # 실제로는 범주형 데이터 인코딩, 스케일링 등 복잡한 전처리 필요
    return np.array([[feature1, feature2]])


# --- 보고서 형식 변환 유틸리티 (개념적) ---

def convert_to_ktfc_report_format(transaction_list: List[Dict[str, Any]]) -> str:
    """
    처리된 트랜잭션 목록을 KTFC 보고 시스템이 요구하는 파일 형식(예: CSV) 문자열로 변환합니다.
    TODO: 실제 KTFC 보고 규격에 맞춰 헤더, 데이터 필드 순서, 푸터 등 구현
    """
    print(f"  [UTIL] KTFC 보고서 형식 변환 중 ({len(transaction_list)} 건)...")
    header = "UTI,ReportingLEI,OtherLEI,AssetClass,ActionType,ExecutionTimestamp,...\n" # 예시 헤더
    body = ""
    # for tx in transaction_list:
    #     # TODO: 각 트랜잭션 데이터를 규격에 맞게 문자열로 변환하여 body에 추가
    #     body += f"{tx.get('unique_transaction_identifier', '')},{tx.get('reporting_counterparty_lei', '')},...\n"
    # return header + body
    return "KTFC_REPORT_CONTENT_SIMULATED" # 가상 보고서 내용 반환


# --- AI 예측 시뮬레이션 (개념적) ---
# 실제로는 별도 AI Inference Service API 호출 또는 모델 직접 로딩 후 predict 호출

def predict_anomaly_with_ensemble_model(features: np.ndarray) -> AnomalyPredictionResult:
     """
     배포된 앙상블 모델을 사용하여 특징 벡터의 이상치 여부를 예측합니다.
     TODO: 실제 AI Inference Service API 호출 또는 로딩된 모델 predict/decision_function 호출
     """
     print("  [UTIL] AI 앙상블 모델 예측 시뮬레이션...")
     # 실제 모델 호출 예시:
     # response = requests.post("http://ai-inference-service/predict_anomaly", json={"features": features.tolist()})
     # result = response.json()
     # return AnomalyPredictionResult(**result)

     # 시뮬레이션 결과 생성
     score = random.uniform(-1, 1)
     prediction_label = "이상치" if score < random.uniform(-0.7, -0.3) else "정상" # 임의의 이상치 판단 확률

     # prediction_label = "이상치" if score < -0.5 else "정상" # 간단한 임계값 판단 예시

     return AnomalyPredictionResult(model_name="EnsembleAnomalyDetector", score=score, prediction_label=prediction_label)


if __name__ == "__main__":
    # 유틸리티 함수 테스트 예시
    today = datetime.date.today()
    now = datetime.datetime.now()
    print(f"Today ({today}): is_weekday={is_weekday(today)}, is_holiday={is_holiday(today)}")
    print(f"Now ({now}): is_business_hours={is_business_hours(now)}")
    print(f"Generated Unique ID: {generate_unique_id()}")
    print(f"Generated Report ID: {generate_report_id('DAILY_KTFC')}")
    print(f"Formatted Date: {format_cftc_date(today)}")
    print(f"Formatted Datetime: {format_cftc_datetime(now)}")

    # AI 예측 시뮬레이션 예시
    # features = np.array([[1000000.0, 0.015]])
    # prediction = predict_anomaly_with_ensemble_model(features)
    # print(f"AI Prediction Simulation: {prediction.model_name}, Score={prediction.score:.4f}, Label={prediction.prediction_label}")
