# src/data-ingestion/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn
# import httpx # 실제 HTTP 호출 시 사용

# src.common에서 로거 및 임시 저장소 가져오기
from common.utils import logger, ingested_data_store

# TODO: Replace direct function calls with actual API calls or message queue publishing
# For demonstration, we simulate calls by directly importing and calling functions
# from other modules. This is NOT how a distributed system should work.
# In a real K8s environment, modules communicate via Services (HTTP/gRPC) or MQ.
from data_processing.main import process_swap_data as call_processing_module

# --- 수신할 데이터 모델 정의 (CFTC Part 45/43 데이터 요소 참고 예시) ---
class SwapData(BaseModel):
    """
    Example model for raw swap trade data received from external systems.
    This should reflect the format of data received from your specific sources.
    """
    trade_id: str = Field(..., description="Internal trade identifier from source system")
    action: str = Field(..., description="Action type (e.g., NEWT, AMND, TERM)")
    instrument_type: str = Field(..., description="Type of swap instrument (e.g., IRS, CDS)")
    asset_class: str = Field(..., description="Asset class (e.g., IR, CR, FX, EQ, CO)")
    effective_date: str = Field(..., description="Swap effective date (YYYY-MM-DD)")
    termination_date: str = Field(..., description="Swap termination date (YYYY-MM-DD)")
    notional_amount: float = Field(..., description="Notional amount of the swap")
    notional_currency: str = Field(..., description="Currency of the notional amount")
    party_a_lei: str = Field(..., description="LEI of party A")
    party_b_lei: str = Field(..., description="LEI of party B")
    price: float | None = Field(None, description="Price or rate")
    price_currency: str | None = Field(None, description="Currency of the price")
    # ... Add other relevant raw data fields

# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/ingest")
async def ingest_swap_data(data: List[SwapData]):
    """
    API endpoint to receive swap trade data from external sources.
    Stores data temporarily and forwards it to the processing module.
    """
    logger.info(f"Received {len(data)} swap data entries for ingestion.")

    # Store received data in the in-memory store
    ingested_data_dicts = [entry.model_dump() for entry in data]
    ingested_data_store.extend(ingested_data_dicts)
    logger.info(f"Stored {len(data)} entries in ingestion store. Total: {len(ingested_data_store)}")

    # Forward data to the processing module
    # In a real system, this would be an async HTTP call or sending to a message queue
    try:
        # Simulate calling the processing module function directly
        # Replace with: await client.post(PROCESSING_MODULE_URL, json=ingested_data_dicts)
        processing_response = await call_processing_module(ingested_data_dicts)
        logger.info(f"Processing module responded: {processing_response}")
        # TODO: Handle processing module response (e.g., check status, log errors)

    except Exception as e:
        logger.error(f"Failed to forward data to processing module: {e}", exc_info=True)
        # TODO: Implement retry logic or move data to a Dead Letter Queue (DLQ)

    return {"status": "success", "received_count": len(data), "processing_status": "forwarded"} # Indicate forwarding initiated

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Data Ingestion module.
    """
    return {"status": "ok", "ingested_count_in_store": len(ingested_data_store)}

# To run this module locally:
# uvicorn main:app --reload --port 8000
