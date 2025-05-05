# src/error-monitoring/main.py

from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn

# src.common에서 로거, 임시 저장소 가져오기
from common.utils import logger, invalid_data_store

# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/report_error")
async def report_error(errors_data: List[Dict[str, Any]]): # Receives error information and related data
    """
    API endpoint to receive and record error information from other modules.
    This is the core of the Error Management module.
    """
    logger.error(f"Received {len(errors_data)} error entries from other modules.")

    for error_entry in errors_data:
        # Assuming error_entry has keys like 'data' and 'errors'
        data = error_entry.get("data", {})
        errors = error_entry.get("errors", [])
        # Attempt to get UTI or source ID for logging
        trade_id = data.get("unique_transaction_identifier", data.get("trade_id", "N/A"))
        source_module = error_entry.get("source_module", "Unknown") # Add source module info in reporting

        logger.error(f"Error reported from {source_module} for ID {trade_id}: Errors: {errors}, Data (partial): {data.get('unique_transaction_identifier')}...") # Log key info

        # TODO: Store error information persistently in a database table
        # This allows querying, tracking status, and building the Admin UI.
        # Example: Save to a 'errors' table with fields:
        # - error_id (PK)
        # - trade_id (or UTI)
        # - source_module
        # - error_messages (JSON list)
        # - raw_data (JSON blob)
        # - timestamp
        # - status (e.g., 'Open', 'Investigating', 'Resolved')
        # - assigned_to (for workflow)

        # For MVP, store in in-memory list
        invalid_data_store.append(error_entry)

        # TODO: Trigger alerts based on error severity or type
        # Example: If critical validation error, send email/Slack notification.
        # Alertmanager (from monitoring stack) can be used for this.

    return {"status": "success", "received_error_count": len(errors_data)}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Error Monitoring module.
    """
    return {"status": "ok", "recorded_error_count_in_store": len(invalid_data_store)}

# TODO: Add API endpoints for the Admin UI (P3)
# - GET /errors: List all recorded errors (with filtering/pagination)
# - GET /errors/{error_id}: Get details of a specific error
# - PUT /errors/{error_id}/status: Update error status (e.g., 'Resolved')
# - POST /errors/{error_id}/retry: Trigger re-processing for a corrected entry

# To run this module locally:
# uvicorn main:app --reload --port 8005
