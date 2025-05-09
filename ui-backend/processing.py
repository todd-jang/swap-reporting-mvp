# ui_backend/processing.py

# import requests # 다른 서비스 API 호출 시 필요
# from common.data_models import ProcessPromptRequest, ProcessPromptResponse, CachedResult, SwapRecord, AnomalyPredictionResult
# from common.utils import predict_anomaly_with_ensemble_model # AI 예측 유틸리티 사용 예시
# from common.db_manager import get_recent_cached_results, save_cached_result, get_swap_record # DB 접근 함수 (개념적)
# from reporting_service import trigger_ad_hoc_report # 임시 보고서 트리거 (개념적)

import uuid
import datetime
from typing import List, Dict, Any
import random # 시뮬레이션용

# --- 가상 데이터 및 서비스 ---
# 실제 DB, AI 서비스, Reporting Service 호출로 대체됩니다.
VIRTUAL_DB = {} # { result_id: CachedResult 객체 }
VIRTUAL_SWAP_RECORDS = {} # { record_id: SwapRecord 객체 }

# 가상 스왑 레코드 몇 개 생성
def create_virtual_swap_records(num: int):
    for i in range(num):
        record_id = f"SWAP_{uuid.uuid4().hex[:8]}"
        record = SwapRecord(
            unique_transaction_identifier=f"UTI_{uuid.uuid4().hex}",
            reporting_counterparty_lei=f"LEI_OUR_{random.randint(1000, 9999)}",
            other_counterparty_lei=f"LEI_CPTY_{random.randint(1000, 9999)}",
            asset_class=random.choice(["IR", "FX", "CR"]),
            swap_type=random.choice(["IRS", "CCS", "CRS"]),
            action_type="NEWT",
            execution_timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 30)),
            effective_date=datetime.date.today() - datetime.timedelta(days=random.randint(1, 30)),
            expiration_date=datetime.date.today() + datetime.timedelta(days=random.randint(365, 365*5)),
            notional_currency_1="USD",
            notional_value_1=random.uniform(1000000, 100000000),
            price=random.uniform(0.001, 0.05),
            variation_margin_collected=random.uniform(1000, 50000) if random.random() > 0.5 else None,
            variation_margin_currency="USD" if random.random() > 0.5 else None,
            ai_anomaly_score=random.uniform(-1.0, 1.0) if random.random() > 0.7 else None,
            ai_prediction_label=random.choice(["정상", "이상치"]) if random.random() > 0.7 else None
        )
        VIRTUAL_SWAP_RECORDS[record_id] = record
create_virtual_swap_records(20)


# --- 비즈니스 로직 함수 ---

async def process_user_prompt(prompt: str) -> ProcessPromptResponse:
    """
    사용자 Prompt를 처리하고 결과를 반환하는 메인 비즈니스 로직 함수.
    다른 서비스(AI, 보고서 등)와 연동됩니다.
    """
    print(f"\n--- Prompt 처리 시작: '{prompt}' ---")
    result_id = uuid.uuid4() # 이 처리 결과의 고유 ID

    # TODO: Prompt 분석 및 처리 로직 구현
    # Prompt의 의도를 파악하여 필요한 작업을 수행합니다.

    # 예시 1: 특정 이상 거래 레코드 조회 요청 프롬프트
    if "이상 거래" in prompt and "조회" in prompt:
         # TODO: DB에서 AI 이상치 플래그된 레코드 조회
         # 예: anomalous_records = db_manager.get_recent_anomalous_records()
         # 가상 데이터에서 이상치 레코드 찾기
         anomalous_records = [r for r in VIRTUAL_SWAP_RECORDS.values() if r.ai_prediction_label == '이상치']

         text_result = f"요청: 이상 거래 조회. 총 {len(anomalous_records)} 건의 잠재적 이상 거래가 탐지되었습니다.\n"
         related_ids = []
         for i, record in enumerate(anomalous_records[:5]): # 최대 5건 예시
              text_result += f"- {record.unique_transaction_identifier}: 자산={record.asset_class}, 금액={record.notional_value_1:.2f} {record.notional_currency_1}, AI점수={record.ai_anomaly_score:.4f}\n"
              related_ids.append(record.unique_transaction_identifier)

         if len(anomalous_records) > 5:
              text_result += f"... 외 {len(anomalous_records) - 5} 건"

         # 결과 캐시 (텍스트 요약)
         text_summary = text_result.split('\n')[0] + "..."
         cache_result(str(result_id), prompt, text_summary, related_ids)

         return ProcessPromptResponse(
             status="Success",
             message="이상 거래 조회가 완료되었습니다.",
             text_result=text_result,
             related_record_ids=related_ids
         )

    # 예시 2: 특정 레코드에 대한 상세 정보 요청 프롬프트
    if "레코드" in prompt and "상세" in prompt:
        # Prompt에서 레코드 ID 추출 로직 필요
        # 예: record_id = extract_record_id_from_prompt(prompt)
        record_id = prompt.split()[-1] # 임시로 프롬프트 마지막 단어를 ID로 간주

        # TODO: DB에서 해당 레코드 조회
        # record = db_manager.get_swap_record(record_id)
        record = VIRTUAL_SWAP_RECORDS.get(record_id) # 가상 데이터 조회

        if record:
             text_result = f"요청: 레코드 {record_id} 상세 정보.\n"
             # TODO: 레코드 상세 정보 포맷팅
             text_result += f"- UTI: {record.unique_transaction_identifier}\n"
             text_result += f"- 보고 주체: {record.reporting_counterparty_lei}\n"
             text_result += f"- 자산/타입: {record.asset_class}/{record.swap_type}\n"
             text_result += f"- 체결일시: {record.execution_timestamp}\n"
             text_result += f"- 명목 금액: {record.notional_value_1:.2f} {record.notional_currency_1}\n"
             text_result += f"- AI 이상치: {record.ai_prediction_label} (점수: {record.ai_anomaly_score:.4f})\n"
             # ... 기타 상세 정보

             # 결과 캐시
             text_summary = f"레코드 {record_id} 상세 정보 조회 결과."
             cache_result(str(result_id), prompt, text_summary, [record_id])


             return ProcessPromptResponse(
                 status="Success",
                 message=f"레코드 {record_id} 상세 정보 조회가 완료되었습니다.",
                 text_result=text_result,
                 related_record_ids=[record_id]
             )
        else:
             return ProcessPromptResponse(
                 status="Failed",
                 message=f"레코드 {record_id}를 찾을 수 없습니다.",
             )


    # 예시 3: 특정 조건의 보고서 생성 요청 프롬프트 (개념적)
    if "보고서" in prompt and "생성" in prompt:
         # TODO: Prompt에서 보고서 조건 (예: 기간, 자산 클래스) 추출
         # TODO: Reporting Service에 보고서 생성 요청 트리거 (비동기)
         # reporting_service.trigger_ad_hoc_report(criteria)
         report_type = "임시 보고서" # 예시
         message = f"요청하신 {report_type} 생성 요청을 처리 중입니다. 완료 시 알림을 보내드립니다."

         # 결과 캐시 (처리 시작 알림)
         text_summary = f"{report_type} 생성 요청 접수."
         cache_result(str(result_id), prompt, text_summary)

         return ProcessPromptResponse(
              status="Processing", # 비동기 작업이므로 Processing 상태 반환
              message=message,
              text_result=text_summary # 중간 결과 또는 알림 메시지 표시
         )


    # 예시 4: AI 모델 재학습 요청 프롬프트 (관리자 권한 필요)
    if "AI 모델" in prompt and "재학습" in prompt:
         # TODO: 사용자 권한 확인 (관리자 등)
         is_authorized = True # 가상 권한 확인

         if is_authorized:
              print("  - AI 모델 재학습 워크플로우 트리거 시뮬레이션...")
              # TODO: AI 학습 서비스에 재학습 요청 트리거 (비동기)
              # ai_learning_service.trigger_model_retrain()
              message = "AI 모델 재학습 워크플로우를 시작합니다. 완료 시 알림을 보내드립니다."

              # 결과 캐시
              text_summary = "AI 모델 재학습 요청 접수."
              cache_result(str(result_id), prompt, text_summary)


              return ProcessPromptResponse(
                   status="Processing",
                   message=message,
                   text_result=text_summary
              )
         else:
              return ProcessPromptResponse(
                   status="Failed",
                   message="AI 모델 재학습 권한이 없습니다."
              )


    # 기본 응답 (Prompt 의도 파악 실패 시)
    print(f"  - Prompt 의도 파악 실패: '{prompt}'")
    text_result = "요청하신 내용을 이해하지 못했습니다. 다른 형식으로 입력해 주시거나 도움말을 참조해 주세요."

    # 결과 캐시
    text_summary = text_result # 이 경우는 요약할 필요 없음
    cache_result(str(result_id), prompt, text_summary)


    return ProcessPromptResponse(
        status="Failed",
        message="Prompt 처리 실패",
        text_result=text_result
    )


# --- 캐시 관리 함수 ---
# 실제 DB에 저장하거나 Redis 등 캐시 시스템 사용

async def get_recent_cached_results(limit: int = 10) -> List[CachedResult]:
    """
    가장 최근 캐시된 결과를 조회합니다.
    """
    print(f"\n--- 최근 캐시 결과 조회 (최대 {limit}개) ---")
    # TODO: DB 또는 캐시 시스템에서 timestamp 기준으로 정렬하여 조회
    # 예: db_manager.query("SELECT * FROM cached_results ORDER BY timestamp DESC LIMIT :limit", params={'limit': limit})

    # 가상 데이터에서 조회 및 정렬
    cached_list = list(VIRTUAL_DB.values())
    cached_list.sort(key=lambda x: x.timestamp, reverse=True)

    print(f"  - 총 {len(cached_list)}개 중 {min(len(cached_list), limit)}개 반환.")
    return cached_list[:limit]

def cache_result(result_id: str, prompt: str, text_summary: str, related_ids: Optional[List[str]] = None):
    """
    처리 결과를 캐시 저장소에 저장합니다.
    """
    print(f"--- 결과 캐시 저장: ID {result_id} ---")
    # TODO: DB 또는 캐시 시스템에 저장
    # 예: db_manager.insert("INSERT INTO cached_results (...) VALUES (...)")
    cached_item = CachedResult(id=result_id, prompt=prompt, text_summary=text_summary, timestamp=datetime.datetime.utcnow())
    VIRTUAL_DB[result_id] = cached_item # 가상 저장소에 저장

    print(f"  - 캐시 저장 완료.")


# --- 기타 도우미 함수 (Prompt 분석 등) ---
def extract_record_id_from_prompt(prompt: str) -> Optional[str]:
     """Prompt 문자열에서 레코드 ID를 추출하는 개념적 함수."""
     # TODO: 자연어 처리 또는 패턴 매칭으로 Prompt에서 레코드 ID 식별 및 추출 로직 구현
     pass
