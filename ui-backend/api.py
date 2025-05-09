# ui_backend/api.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
# from common.data_models import ProcessPromptRequest, ProcessPromptResponse, CachedResult
# from ui_backend.processing import process_user_prompt, get_recent_cached_results

# common.data_models 및 ui_backend.processing 을 import 할 수 있도록 PYTHONPATH 설정 또는 실행 환경 구성 필요
# 예시를 위해 현재 디렉토리에서 상대 경로 import 시도 (실제 프로덕션 코드에서는 적절한 패키지 구조 및 import 필요)

try:
    # common 모듈이 상위 디렉토리에 있다고 가정하고 상대 경로 import
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

    from common.data_models import ProcessPromptRequest, ProcessPromptResponse, CachedResult
    from ui_backend.processing import process_user_prompt, get_recent_cached_results

except ImportError as e:
    print(f"Import Error: {e}")
    print("Please ensure common and ui_backend modules are correctly placed and PYTHONPATH is set.")
    # 임시로 클래스 정의 (실제 로직은 작동 안 함)
    class ProcessPromptRequest: pass
    class ProcessPromptResponse: pass
    class CachedResult: pass
    async def process_user_prompt(prompt): return ProcessPromptResponse(status="Failed", message="Import Error in backend logic")
    async def get_recent_cached_results(limit): return []


app = FastAPI(
    title="Swap Reporting MVP UI Backend API",
    description="API for user interaction with the Swap Reporting MVP system.",
    version="0.1.0",
)

@app.post("/process_prompt", response_model=ProcessPromptResponse)
async def handle_process_prompt(request: ProcessPromptRequest):
    """
    사용자 Prompt를 받아 시스템에서 처리합니다.
    """
    print(f"\n--- API: /process_prompt 호출 ---")
    try:
        # processing.py 의 비즈니스 로직 함수 호출
        response = await process_user_prompt(request.prompt)
        print("--- API: Prompt 처리 응답 반환 ---")
        return response
    except Exception as e:
        print(f"--- API 오류: /process_prompt - {e} ---")
        # TODO: 적절한 오류 로깅 및 처리
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

@app.get("/cached_results", response_model=List[CachedResult])
async def get_cached_results(limit: int = 10):
    """
    최근 캐시된 결과 목록을 조회합니다.
    """
    print(f"\n--- API: /cached_results 호출 (limit={limit}) ---")
    try:
        # processing.py 의 캐시 조회 함수 호출
        cached_list = await get_recent_cached_results(limit=limit)
        print("--- API: 캐시 결과 목록 응답 반환 ---")
        return cached_list
    except Exception as e:
        print(f"--- API 오류: /cached_results - {e} ---")
        # TODO: 적절한 오류 로깅 및 처리
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")

# --- 기타 API 엔드포인트 예시 ---
# @app.get("/record/{record_id}", response_model=SwapRecord)
# async def get_swap_record_by_id(record_id: str):
#     """특정 스왑 레코드 상세 정보를 조회합니다."""
#     # TODO: DB에서 레코드 조회 로직 호출
#     pass

# @app.post("/review_anomaly/{record_id}")
# async def submit_anomaly_review(record_id: str, review_status: str, comments: Optional[str] = None):
#     """이상 거래 검토 결과를 제출합니다."""
#     # TODO: 검토 결과 DB 업데이트, 정정 보고 트리거 로직 호출
#     pass


# --- 애플리케이션 실행 (개발용) ---
# 실제 배포 시에는 uvicorn과 같은 ASGI 서버를 사용합니다.
# if __name__ == "__main__":
#     import uvicorn
#     print("\nFastAPI 애플리케이션 실행 중 (개발 모드)...")
#     uvicorn.run(app, host="0.0.0.0", port=8000)
#     print("FastAPI 애플리케이션 종료.")
