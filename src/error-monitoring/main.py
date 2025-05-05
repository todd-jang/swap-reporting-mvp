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


#=================== with DB
# src/error-monitoring/main.py

from fastapi import FastAPI, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime
import uuid # To generate unique IDs for errors
import os # To read environment variables

# --- SQLAlchemy Imports ---
from sqlalchemy.orm import Session
from sqlalchemy import desc # For sorting

# src.common에서 로거, DB 설정 및 모델 가져오기
from common.utils import logger, get_db, ErrorRecord, create_database_tables # Import get_db and ErrorRecord
from common.utils import send_alert # Import alert utility

# --- Ensure database tables are created on startup (for local dev) ---
# In production, handle migrations separately
create_database_tables()

# TODO: Replace hardcoded URLs with Environment Variables if calling other services (e.g., for retry)
# PROCESSING_MODULE_URL = os.environ.get("PROCESSING_MODULE_URL", "http://data-processing-service:80/process") # Example in K8s
PROCESSING_MODULE_URL = os.environ.get("PROCESSING_MODULE_URL", "http://localhost:8001/process") # Default to Local testing URL for retry simulation
INGESTION_MODULE_URL = os.environ.get("INGESTION_MODULE_URL", "http://localhost:8000/ingest") # Default to Local testing URL for retry simulation


# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

# --- P1: 오류 수신 및 기록 엔드포인트 ---
@app.post("/report_error")
async def report_error(errors_data: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """
    API endpoint to receive and record error information from other modules.
    Stores errors persistently in the database.
    """
    logger.error(f"Received {len(errors_data)} error entries from other modules.")

    new_error_records = []
    for error_entry in errors_data:
        try:
            # Assuming error_entry has keys like 'data' and 'errors' and 'source_module'
            data_payload = error_entry.get("data", {})
            errors = error_entry.get("errors", [])
            source_module = error_entry.get("source_module", "Unknown")
            original_source_data_payload = data_payload.get("original_source_data") # Get original raw data if available

            # Attempt to get UTI or source ID for logging and storage
            trade_id = data_payload.get("unique_transaction_identifier", data_payload.get("trade_id", "N/A"))
            error_messages = errors if isinstance(errors, list) else [str(errors)] # Ensure errors is a list of strings

            logger.error(f"Error reported from {source_module} for ID {trade_id}: Errors: {error_messages}")

            # Create a database model instance for the error record
            db_error_record = ErrorRecord(
                trade_id=trade_id,
                source_module=source_module,
                error_messages=error_messages,
                data_payload=data_payload, # Store the data associated with the error
                original_source_data_payload=original_source_data_payload, # Store original raw data if available
                timestamp=datetime.utcnow(),
                status="Open", # Initial status
                severity="Error" # Default severity, could be passed from source module
            )
            new_error_records.append(db_error_record)

            # TODO: Trigger alerts based on error severity or type
            # send_alert(db_error_record.severity, f"New Error in {source_module} for {trade_id}", {"error_id": db_error_record.id, "uti": trade_id, "module": source_module, "errors": error_messages}) # Uncomment to send alerts

        except Exception as e:
             logger.error(f"Critical error while processing received error entry: {e}", exc_info=True)
             send_alert("Critical", f"Internal error processing received error: {e}", {"module": "error-monitoring", "received_data_sample": str(error_entry)[:200]}) # Avoid logging full data in alert


    # Simulate storing error records in the database
    try:
        db.add_all(new_error_records)
        db.commit()
        # Refresh records to get generated IDs for alerts if needed
        # for record in new_error_records:
        #     db.refresh(record)
        logger.info(f"Successfully simulated storing {len(new_error_records)} error records in error_records table.")
        recorded_count = len(new_error_records)

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store error records in database: {e}", exc_info=True)
        send_alert("Critical", f"Database error storing errors: {e}", {"module": "error-monitoring", "error": str(e)})
        # This is a critical failure in the error monitoring itself
        recorded_count = 0 # Indicate that storage failed


    return {"status": "success", "received_error_count": len(errors_data), "recorded_error_count": recorded_count}

# --- P3: Admin UI를 위한 API 엔드포인트 ---

@app.get("/errors")
async def list_errors(
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None, description="Filter by error status (e.g., Open, Resolved)"),
    source_module: Optional[str] = Query(None, description="Filter by source module"),
    trade_id: Optional[str] = Query(None, description="Filter by trade ID or UTI (partial match)"),
    limit: int = Query(100, description="Maximum number of errors to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    API endpoint to list recorded errors (for Admin UI).
    Supports filtering and pagination. Fetches from the database.
    """
    logger.info(f"Received request to list errors with filters: status={status}, module={source_module}, trade_id={trade_id}, limit={limit}, offset={offset}")

    # Build SQLAlchemy query
    query = db.query(ErrorRecord)

    if status:
        query = query.filter(ErrorRecord.status == status)
    if source_module:
        query = query.filter(ErrorRecord.source_module == source_module)
    if trade_id:
        # Use ilike for case-insensitive partial match
        query = query.filter(ErrorRecord.trade_id.ilike(f"%{trade_id}%"))

    # Get total count before applying limit/offset
    total_count = query.count()

    # Apply ordering, limit, and offset
    errors = query.order_by(desc(ErrorRecord.timestamp)).offset(offset).limit(limit).all()

    # Convert SQLAlchemy objects to dictionaries for response (excluding sensitive raw_payload if needed)
    error_list = []
    for error in errors:
        error_dict = error.__dict__
        error_dict.pop('_sa_instance_state', None) # Remove SQLAlchemy internal state
        # TODO: Optionally redact sensitive data from data_payload or original_source_data_payload
        error_list.append(error_dict)

    logger.info(f"Found {total_count} matching errors. Returning {len(error_list)} after pagination.")

    return {
        "status": "success",
        "total_count": total_count,
        "returned_count": len(error_list),
        "offset": offset,
        "limit": limit,
        "errors": error_list
    }

@app.get("/errors/{error_id}")
async def get_error_details(error_id: str, db: Session = Depends(get_db)):
    """
    API endpoint to get details of a specific error (for Admin UI). Fetches from the database.
    """
    logger.info(f"Received request for error details: {error_id}")

    # Query the database by error_id
    error = db.query(ErrorRecord).filter(ErrorRecord.id == error_id).first()

    if error:
        logger.info(f"Found error details for {error_id}.")
        error_dict = error.__dict__
        error_dict.pop('_sa_instance_state', None)
        # TODO: Optionally redact sensitive data
        return {"status": "success", "error": error_dict}

    logger.warning(f"Error with ID {error_id} not found.")
    raise HTTPException(status_code=404, detail="Error not found")

@app.put("/errors/{error_id}/status")
async def update_error_status(error_id: str, new_status: str, db: Session = Depends(get_db)):
    """
    API endpoint to update the status of an error (for Admin UI). Updates in the database.
    e.g., new_status can be 'Investigating', 'Resolved', 'Closed'.
    """
    logger.info(f"Received request to update status for error {error_id} to {new_status}")

    # Find the error record in the database
    error = db.query(ErrorRecord).filter(ErrorRecord.id == error_id).first()

    if error:
        logger.info(f"Updating status for error {error_id} from {error.status} to {new_status}.")
        error.status = new_status
        db.commit() # Commit the status change
        db.refresh(error) # Refresh to get the updated state if needed
        # TODO: Log the status change with timestamp and user (if authentication is added)
        error_dict = error.__dict__
        error_dict.pop('_sa_instance_state', None)
        return {"status": "success", "error": error_dict}

    logger.warning(f"Error with ID {error_id} not found for status update.")
    raise HTTPException(status_code=404, detail="Error not found")

@app.post("/errors/{error_id}/retry")
async def retry_error_processing(error_id: str, db: Session = Depends(get_db)):
    """
    API endpoint to trigger re-processing for a specific error (for Admin UI).
    Retrieves data from the database and re-injects it into the pipeline.
    """
    logger.info(f"Received request to retry processing for error {error_id}")

    # Find the error record in the database
    error_to_retry = db.query(ErrorRecord).filter(ErrorRecord.id == error_id).first()

    if not error_to_retry:
        logger.warning(f"Error with ID {error_id} not found for retry.")
        raise HTTPException(status_code=404, detail="Error not found")

    # Determine which data to re-inject based on where the error occurred
    source_module = error_to_retry.source_module
    data_payload = error_to_retry.data_payload # This is the data received by the module that reported the error
    original_raw_data_payload = error_to_retry.original_source_data_payload # Original raw data if available

    if not data_payload and not original_raw_data_payload:
        logger.error(f"No data payload found for retry for error {error_id}.")
        raise HTTPException(status_code=400, detail="No data associated with this error to retry")

    logger.info(f"Attempting to re-inject data for error {error_id} (Source Module: {source_module}).")

    # --- Implement the actual re-injection logic ---
    # This is complex and depends on your pipeline design and where the error occurred.
    # We need to send the correct data payload to the correct module's API.

    retry_target_url = None
    data_to_send = None # Data payload to send in the HTTP request

    if source_module == "data-ingestion":
        # If ingestion failed, retry ingestion. Need original raw data.
        retry_target_url = INGESTION_MODULE_URL
        if original_raw_data_payload:
             # Ingestion expects a list of raw data dicts
             data_to_send = [original_raw_data_payload]
        elif data_payload:
             # If original_raw_data_payload is not stored, try using data_payload
             # This assumes data_payload for ingestion error is the raw data.
             data_to_send = [data_payload]
        else:
             logger.error(f"No suitable data found to retry ingestion error {error_id}.")
             raise HTTPException(status_code=400, detail="No raw data available for ingestion retry")

    elif source_module == "data-processing":
        # If processing failed, retry processing. Need raw data.
        retry_target_url = PROCESSING_MODULE_URL
        if original_raw_data_payload:
             # Processing expects a list of raw data dicts
             data_to_send = [original_raw_data_payload]
        elif data_payload and 'trade_id' in data_payload: # Check if data_payload looks like raw data
             data_to_send = [data_payload]
        else:
            logger.error(f"No suitable raw data found to retry processing error {error_id}.")
            raise HTTPException(status_code=400, detail="No raw data available for processing retry")


    elif source_module == "validation":
        # If validation failed, retry processing. Need raw data.
        # Retrying from processing is safer as validation depends on processing output.
        retry_target_url = PROCESSING_MODULE_URL
        if original_raw_data_payload:
             # Processing expects a list of raw data dicts
             data_to_send = [original_raw_data_payload]
        elif data_payload and 'trade_id' in data_payload: # Check if data_payload looks like raw data
             data_to_send = [data_payload]
        elif data_payload and 'unique_transaction_identifier' in data_payload: # data_payload might be processed data
             # If original raw data is not available, we could try sending processed data to processing,
             # but this might cause issues if processing is not idempotent or expects raw format.
             # A safer retry point is usually the start of the pipeline (Ingestion) or Processing.
             # Let's prioritize original raw data if available.
             logger.warning(f"Original raw data not available for validation error {error_id}. Attempting retry with processed data payload.")
             data_to_send = [data_payload] # Send processed data payload
             # Note: Processing module MUST be able to handle this if original raw is unavailable.

        else:
            logger.error(f"No suitable data found to retry validation error {error_id}.")
            raise HTTPException(status_code=400, detail="No data available for validation retry")

    # TODO: Add retry logic for Report Generation and Report Submission errors (P2/P3)
    # If Report Generation failed, retry generation with processed data.
    # If Report Submission failed, retry submission with the generated report file info.


    if not retry_target_url or not data_to_send:
         logger.error(f"Could not determine retry target or data for error {error_id}.")
         raise HTTPException(status_code=500, detail="Could not determine retry strategy for this error")


    logger.info(f"Simulating sending data for retry to {retry_target_url}")

    try:
        async with httpx.AsyncClient() as client:
            # Using client.post for demonstration. MQ is better for reliability.
            response = await client.post(retry_target_url, json=data_to_send, timeout=60.0)
            response.raise_for_status()
            logger.info(f"Successfully initiated retry for error {error_id}. Target: {retry_target_url}. Response: {response.json()}")

            # TODO: Update error status to 'Retrying' or 'Resolved' if retry is successful (requires async update based on downstream success)
            # For now, just log success. A better approach is to have downstream modules report back success/failure of retried data.
            # Or update status to 'Retrying' immediately and have a separate process monitor retries.
            # Let's update status to 'Retrying' for now.
            error_to_retry.status = "Retrying"
            db.commit()
            db.refresh(error_to_retry)

            return {"status": "success", "error_id": error_id, "retry_status": "initiated", "target_url": retry_target_url}

    except httpx.RequestError as exc:
        logger.error(f"Failed to initiate retry for error {error_id}: {exc}", exc_info=True)
        send_alert("Error", f"Failed to initiate retry for error {error_id}: {exc}", {"module": "error-monitoring", "error_id": error_id, "error": str(exc), "target_url": retry_target_url})
        # TODO: Update error status to 'Retry Failed'
        raise HTTPException(status_code=500, detail=f"Failed to initiate retry: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during retry initiation for error {error_id}: {e}", exc_info=True)
        send_alert("Critical", f"Unexpected error initiating retry for error {error_id}: {e}", {"module": "error-monitoring", "error_id": error_id, "error": str(e)})
        # TODO: Update error status to 'Retry Failed'
        raise HTTPException(status_code=500, detail=f"Unexpected error initiating retry: {e}")


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for the Error Monitoring module.
    Checks database connectivity.
    """
    try:
        # Attempt to query the database to check connectivity
        db.query(ErrorRecord).limit(1).all()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
        logger.error(f"Database health check failed: {e}", exc_info=True)
        send_alert("Critical", f"Database connectivity issue in Error Monitoring: {e}", {"module": "error-monitoring", "check": "db_connectivity"})

    return {"status": "ok", "database_status": db_status}

# To run this module locally:
# 1. Ensure your database is running.
# 2. Set the DATABASE_URL environment variable if not using SQLite.
# 3. Run uvicorn: uvicorn main:app --reload --port 8005
