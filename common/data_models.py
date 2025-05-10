#from ui-backend/common
# common/data_models.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime

# --- 기본 스왑 데이터 모델 (CFTC 규정 기반 필드 일부 예시) ---
class SwapRecord(BaseModel):
    """
    단일 스왑 거래 레코드 데이터를 나타내는 모델.
    CFTC 규정에서 요구하는 주요 필드를 포함합니다.
    """
    unique_transaction_identifier: str = Field(..., description="UTI (Unique Transaction Identifier)")
    reporting_counterparty_lei: str = Field(..., description="보고 주체 LEI")
    other_counterparty_lei: str = Field(..., description="상대방 LEI")
    platform_id: Optional[str] = Field(None, description="거래 플랫폼 ID")
    asset_class: str = Field(..., description="자산 클래스 (예: IR, FX, CR)")
    swap_type: str = Field(..., description="스왑 타입 (예: IRS, CCS)")
    action_type: str = Field(..., description="보고 행위 (예: NEWT, POST)")
    execution_timestamp: datetime.datetime = Field(..., description="체결 타임스탬프 (UTC)")
    effective_date: datetime.date = Field(..., description="효력 발생일")
    expiration_date: datetime.date = Field(..., description="만기일")
    notional_currency_1: str = Field(..., description="명목 원금 통화 1")
    notional_value_1: float = Field(..., description="명목 원금 금액 1")
    notional_currency_2: Optional[str] = Field(None, description="명목 원금 통화 2 (통화 스왑 등)")
    notional_value_2: Optional[float] = Field(None, description="명목 원금 금액 2")
    price: Optional[float] = Field(None, description="거래 가격 또는 이율")
    price_currency: Optional[str] = Field(None, description="가격 통화")
    variation_margin_collected: Optional[float] = Field(None, description="징수 변동 증거금")
    variation_margin_currency: Optional[str] = Field(None, description="변동 증거금 통화")
    # ... (CFTC 규정의 다른 필수/조건부 필드 추가)

    # --- AI 관련 필드 (시스템 내부 관리) ---
    ai_anomaly_score: Optional[float] = Field(None, description="AI 이상치 탐지 점수")
    ai_prediction_label: Optional[str] = Field(None, description="AI 예측 라벨 (예: '정상', '이상치')")
    manual_review_status: str = Field("Pending", description="수동 검토 상태 (Pending, Approved, Rejected, Corrected)")
    reviewer_comments: Optional[str] = Field(None, description="검토자 의견")
    correction_status: str = Field("NotNeeded", description="정정 보고 상태 (NotNeeded, Required, Submitted, Failed)")
    processed_timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, description="시스템 처리 타임스탬프 (UTC)")


# --- AI 예측 결과 모델 ---
class AnomalyPredictionResult(BaseModel):
    """
    AI 이상치 탐지 모델의 예측 결과 모델.
    """
    model_name: str
    score: float # 이상치 점수
    prediction_label: str # 예: '정상', '이상치'


# --- UI 백엔드 요청/응답 모델 ---
class ProcessPromptRequest(BaseModel):
    """
    UI로부터 Prompt 처리를 요청하는 모델.
    """
    prompt: str = Field(..., description="사용자 입력 Prompt")


class ProcessPromptResponse(BaseModel):
    """
    UI 백엔드의 Prompt 처리 결과를 반환하는 모델.
    """
    status: str = Field(..., description="처리 상태 (예: 'Success', 'Failed', 'Processing')")
    message: Optional[str] = Field(None, description="상태 메시지")
    text_result: Optional[str] = Field(None, description="텍스트 결과 (요약 리포트 등)")
    audio_url: Optional[str] = Field(None, description="음성 결과 파일 URL")
    related_record_ids: Optional[List[str]] = Field(None, description="결과와 관련된 스왑 레코드 ID 목록")


class CachedResult(BaseModel):
    """
    UI 하단에 표시될 캐시된 결과 목록 항목 모델.
    """
    id: str = Field(..., description="캐시된 결과 고유 ID") # 예: UUID
    prompt: str = Field(..., description="원래 Prompt")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, description="결과 생성 타임스탬프")
    text_summary: str = Field(..., description="텍스트 결과 요약 또는 스니펫")
    # 필요시 다른 메타데이터 추가 (예: 관련 레코드 수 등)


# --- 보고서 및 알림 관련 모델 (개념적) ---
class AnomalyReport(BaseModel):
    """
    이상 거래 보고서 모델 (내부 사용 또는 외부 전송용).
    """
    report_id: str
    timestamp: datetime.datetime
    anomalous_records: List[SwapRecord] # 이상 거래 레코드 목록
    analysis_summary: str # 분석 결과 요약
    # ... (다른 보고서 필드)

class AlertNotification(BaseModel):
    """
    알림 메시지 모델.
    """
    alert_id: str
    timestamp: datetime.datetime
    severity: str # 예: 'Critical', 'Warning'
    message: str # 알림 내용
    related_ids: Optional[List[str]] = None # 관련 레코드/보고서 ID


# --- 워크플로우 및 배치 처리 관련 모델 (개념적) ---
class BatchJobStatus(BaseModel):
    """
    배치 작업 상태 모델.
    """
    job_id: str
    job_name: str
    status: str # 예: 'Pending', 'Running', 'Completed', 'Failed'
    start_time: Optional[datetime.datetime]
    end_time: Optional[datetime.datetime]
    progress: float # 0.0 ~ 1.0
    # ... (다른 상태 정보)
