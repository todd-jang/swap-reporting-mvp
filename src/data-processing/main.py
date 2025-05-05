# src/data-processing/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn
# import httpx # 실제 HTTP 호출 시 사용

# src.common에서 로거, 임시 저장소, 유틸 함수 가져오기
from common.utils import logger, ingested_data_store, processed_data_store, generate_uti, validate_lei

# TODO: Replace direct function calls with actual API calls or message queue publishing
from validation.main import validate_swap_data as call_validation_module
from error_monitoring.main import report_error as call_error_monitor_module

# --- 처리/정규화 후 데이터 모델 정의 (CFTC Part 45/43 CDE 참고 예시) ---
class ProcessedSwapData(BaseModel):
    """
    Example model for processed and standardized swap trade data.
    Includes Common Data Elements (CDE) and internal processing results.
    """
    unique_transaction_identifier: str = Field(..., description="Unique Transaction Identifier (UTI)")
    reporting_counterparty_lei: str = Field(..., description="LEI of the reporting counterparty")
    other_counterparty_lei: str = Field(..., description="LEI of the other counterparty")
    action_type: str = Field(..., description="Action type (e.g., NEWT, AMND, TERM)")
    event_type: str | None = Field(None, description="Life cycle event type (e.g., COMP, EXCH)") # Life cycle event type
    asset_class: str = Field(..., description="Asset class")
    # ... (UPI, Venue, Execution Timestamp etc. CDE fields based on regulation)
    effective_date: str = Field(..., description="Effective date (YYYY-MM-DD)")
    termination_date: str = Field(..., description="Termination date (YYYY-MM-DD)")
    notional_amount: float = Field(..., description="Notional amount (standardized currency)")
    notional_currency: str = Field(..., description="Currency of the notional amount (standardized)")
    # ... (Add other relevant fields like price, collateral, margin - refer to document pages 59-61)

    # Internal processing status/flags
    processing_status: str = "Processed"
    processing_errors: List[str] = []


# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/process")
async def process_swap_data(data: List[Dict[str, Any]]): # Receives data as Dict from Ingestion module (simulated)
    """
    API endpoint to process and standardize received swap trade data.
    Generates identifiers, performs basic transformations, and forwards to validation.
    """
    logger.info(f"Received {len(data)} data entries for processing from Ingestion.")

    processed_data_list: List[ProcessedSwapData] = []
    processing_failed_entries: List[Dict[str, Any]] = [] # To track entries that failed processing

    for entry in data:
        source_trade_id = entry.get("trade_id", "N/A")
        logger.info(f"Processing entry with source ID: {source_trade_id}")
        processing_errors = []
        processed_entry_dict = {}

        try:
            # --- Core Processing and Normalization Logic ---
            # 1. Map raw data fields to standard CDE fields
            # 2. Generate UTI
            # 3. Standardize values (e.g., currency codes to uppercase, dates to YYYY-MM-DD)
            # 4. Perform basic data type conversions
            # 5. Perform basic LEI format validation (more detailed validation in validation module)

            generated_uti = generate_uti(entry) # Generate UTI
            reporting_lei = entry.get("party_a_lei", "").strip().upper()
            other_lei = entry.get("party_b_lei", "").strip().upper()
            notional_amt = float(entry.get("notional_amount", 0)) if entry.get("notional_amount") is not None else None
            notional_ccy = entry.get("notional_currency", "").strip().upper()

            # Basic LEI format check during processing
            if not validate_lei(reporting_lei):
                 processing_errors.append(f"Reporting Counterparty LEI '{reporting_lei}' has invalid format.")
            if not validate_lei(other_lei):
                 processing_errors.append(f"Other Counterparty LEI '{other_lei}' has invalid format.")

            # Basic Notional check during processing
            if notional_amt is None or notional_amt < 0:
                 processing_errors.append(f"Notional Amount '{notional_amt}' is invalid.")


            processed_entry_dict = {
                "unique_transaction_identifier": generated_uti,
                "reporting_counterparty_lei": reporting_lei,
                "other_counterparty_lei": other_lei,
                "action_type": entry.get("action", "").strip().upper(),
                "event_type": None, # Logic for life cycle events needed
                "asset_class": entry.get("asset_class", "").strip().upper(),
                "effective_date": entry.get("effective_date", "").strip(), # Date format validation needed
                "termination_date": entry.get("termination_date", "").strip(), # Date format validation needed
                "notional_amount": notional_amt,
                "notional_currency": notional_ccy,
                # ... Map other fields ...
                "processing_status": "Processed" if not processing_errors else "Processing Failed",
                "processing_errors": processing_errors
            }

            # Create Pydantic model instance
            processed_entry = ProcessedSwapData(**processed_entry_dict)
            processed_data_list.append(processed_entry)

            if processing_errors:
                 processing_failed_entries.append({"source_data": entry, "processing_errors": processing_errors})


        except Exception as e:
            logger.error(f"Critical error processing entry with source ID {source_trade_id}: {e}", exc_info=True)
            processing_failed_entries.append({"source_data": entry, "processing_errors": [f"Critical Processing Error: {e}"]})
            # TODO: Send critical processing failures to error monitor immediately

    logger.info(f"Finished processing {len(data)} entries. Generated {len(processed_data_list)} processed entries with {len(processing_failed_entries)} failures.")

    # Store processed data (including those with processing errors)
    processed_data_store.extend([entry.model_dump() for entry in processed_data_list])
    logger.info(f"Stored {len(processed_data_list)} entries in processed data store. Total: {len(processed_data_store)}")

    # Forward successfully processed data (even if they have processing_errors logged) to validation module
    # The validation module will perform comprehensive validation.
    if processed_data_list:
        logger.info(f"Forwarding {len(processed_data_list)} entries to validation module.")
        try:
            # Simulate calling the validation module function directly
            # Replace with: await client.post(VALIDATION_MODULE_URL, json=[entry.model_dump() for entry in processed_data_list])
            validation_response = await call_validation_module(processed_data_list)
            logger.info(f"Validation module responded: {validation_response}")
            # TODO: Handle validation module response

        except Exception as e:
            logger.error(f"Failed to forward data to validation module: {e}", exc_info=True)
            # TODO: Implement retry logic or move data to DLQ

    # TODO: Handle entries that failed critical processing (processing_failed_entries)
    if processing_failed_entries:
        logger.error(f"Reporting {len(processing_failed_entries)} critical processing failures to error monitor.")
        try:
            # Simulate calling the error monitor module function directly
            # Replace with: await client.post(ERROR_MONITOR_MODULE_URL, json=processing_failed_entries)
            error_monitor_response = await call_error_monitor_module(processing_failed_entries)
            logger.info(f"Error monitor module responded: {error_monitor_response}")
        except Exception as e:
            logger.error(f"Failed to report processing failures to error monitor: {e}", exc_info=True)


    return {"status": "success", "processed_count": len(processed_data_list), "processing_failed_count": len(processing_failed_entries), "validation_status": "forwarded"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Data Processing module.
    """
    return {"status": "ok", "processed_count_in_store": len(processed_data_store)}

# To run this module locally:
# uvicorn main:app --reload --port 8001


#===================== realworld 
# src/data-processing/main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn
import httpx
import os # To read environment variables

# --- SQLAlchemy Imports ---
from sqlalchemy.orm import Session
from sqlalchemy import select # For selecting data

# src.common에서 로거, DB 설정 및 모델 가져오기
from common.utils import logger, get_db, ProcessedSwapDataDB, RawIngestedData, create_database_tables # Import DB model
from common.utils import generate_uti, validate_lei, send_alert # Import utilities

# --- Ensure database tables are created on startup (for local dev) ---
# In production, handle migrations separately
# create_database_tables() # Already called in ingestion/error_monitoring, ensure it's run once

# TODO: Replace hardcoded URLs with Environment Variables injected by Kubernetes
# VALIDATION_MODULE_URL = os.environ.get("VALIDATION_MODULE_URL", "http://validation-service:80/validate") # Example in K8s
# ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://error-monitoring-service:80/report_error") # Example in K8s
VALIDATION_MODULE_URL = os.environ.get("VALIDATION_MODULE_URL", "http://localhost:8002/validate") # Default to Local testing URL
ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://localhost:8005/report_error") # Default to Local testing URL


# --- 처리/정규화 후 데이터 모델 정의 (CFTC Part 45/43 CDE 참고 예시) ---
# This Pydantic model is used for API input/output, not directly for DB mapping
class ProcessedSwapData(BaseModel):
    """
    Example model for processed and standardized swap trade data.
    Includes Common Data Elements (CDE) and internal processing results.
    """
    unique_transaction_identifier: str = Field(..., description="Unique Transaction Identifier (UTI)")
    reporting_counterparty_lei: str = Field(..., description="LEI of the reporting counterparty")
    other_counterparty_lei: str = Field(..., description="LEI of the other counterparty")
    action_type: str = Field(..., description="Action type (e.g., NEWT, AMND, TERM)")
    event_type: str | None = Field(None, description="Life cycle event type (e.g., COMP, EXCH)") # Life cycle event type
    asset_class: str = Field(..., description="Asset class")
    # ... (UPI, Venue, Execution Timestamp etc. CDE fields based on regulation)
    effective_date: str = Field(..., description="Effective date (YYYY-MM-DD)")
    termination_date: str = Field(..., description="Termination date (YYYY-MM-DD)")
    notional_amount: float | None = Field(None, description="Notional amount (standardized currency)") # Allow None if processing fails
    notional_currency: str | None = Field(None, description="Currency of the notional amount (standardized)") # Allow None if processing fails
    price: float | None = Field(None, description="Price or rate (standardized)")
    price_currency: str | None = Field(None, description="Currency of the price (standardized)")
    # ... (Add other relevant fields like collateral, margin - refer to document pages 59-61)

    # Internal processing status/flags - These might not be in the DB model but added during processing
    processing_status: str = "Processed"
    processing_errors: List[str] = []
    original_raw_data_id: Optional[str] = Field(None, description="Link to the original raw data record")


# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/process")
async def process_swap_data(data: List[Dict[str, Any]], db: Session = Depends(get_db)): # Receives data as Dict from Ingestion module
    """
    API endpoint to process and standardize received swap trade data.
    Generates identifiers, performs basic transformations, stores processed data,
    and forwards to validation.
    """
    logger.info(f"Received {len(data)} data entries for processing from Ingestion.")

    processed_data_list: List[ProcessedSwapDataDB] = [] # SQLAlchemy models for DB
    data_for_validation: List[ProcessedSwapData] = [] # Pydantic models for next module
    processing_failed_for_reporting: List[Dict[str, Any]] = [] # Entries that failed processing to report

    for entry in data:
        source_trade_id = entry.get("trade_id", "N/A")
        # Assuming the ingestion module passes the DB ID of the raw record if available
        original_raw_db_id = entry.get("id") # Attempt to get the DB ID from the dict

        logger.info(f"Processing entry with source ID: {source_trade_id}, Raw DB ID: {original_raw_db_id}")
        processing_errors = []
        processed_entry_dict = {}

        try:
            # --- Core Processing and Normalization Logic ---
            # 1. Map raw data fields to standard CDE fields
            # 2. Generate UTI
            # 3. Standardize values (e.g., currency codes to uppercase, dates to YYYY-MM-DD)
            # 4. Perform basic data type conversions
            # 5. Perform basic LEI format validation (more detailed validation in validation module)

            generated_uti = generate_uti(entry) # Generate UTI
            reporting_lei = entry.get("party_a_lei", "").strip().upper()
            other_lei = entry.get("party_b_lei", "").strip().upper()

            # Safely convert notional amount and price, handle potential errors
            notional_amt = None
            try:
                if entry.get("notional_amount") is not None:
                    notional_amt = float(entry["notional_amount"])
            except (ValueError, TypeError):
                processing_errors.append(f"Invalid Notional Amount format: {entry.get('notional_amount')}")
                send_alert("Warning", f"Invalid Notional Amount format for source ID {source_trade_id}", {"module": "data-processing", "field": "notional_amount", "value": entry.get('notional_amount'), "raw_db_id": original_raw_db_id})


            price_val = None
            try:
                if entry.get("price") is not None:
                     price_val = float(entry["price"])
            except (ValueError, TypeError):
                 processing_errors.append(f"Invalid Price format: {entry.get('price')}")
                 send_alert("Warning", f"Invalid Price format for source ID {source_trade_id}", {"module": "data-processing", "field": "price", "value": entry.get('price'), "raw_db_id": original_raw_db_id})


            # Basic LEI format check during processing
            if not validate_lei(reporting_lei):
                 processing_errors.append(f"Reporting Counterparty LEI '{reporting_lei}' has invalid format.")
                 send_alert("Warning", f"Invalid Reporting Counterparty LEI format for source ID {source_trade_id}", {"module": "data-processing", "lei": reporting_lei, "raw_db_id": original_raw_db_id})

            if not validate_lei(other_lei):
                 processing_errors.append(f"Other Counterparty LEI '{other_lei}' has invalid format.")
                 send_alert("Warning", f"Invalid Other Counterparty LEI format for source ID {source_trade_id}", {"module": "data-processing", "lei": other_lei, "raw_db_id": original_raw_db_id})

            # Basic Notional check during processing
            if notional_amt is not None and notional_amt < 0:
                 processing_errors.append(f"Negative Notional Amount for source ID {source_trade_id}")
                 send_alert("Warning", f"Negative Notional Amount for source ID {source_trade_id}", {"module": "data-processing", "notional_amount": notional_amt, "raw_db_id": original_raw_db_id})


            # Create SQLAlchemy DB model instance
            db_processed_entry = ProcessedSwapDataDB(
                unique_transaction_identifier = generated_uti,
                reporting_counterparty_lei = reporting_lei,
                other_counterparty_lei = other_lei,
                action_type = entry.get("action", "").strip().upper(),
                event_type = None, # Logic for life cycle events needed (P2/P3)
                asset_class = entry.get("asset_class", "").strip().upper(),
                effective_date = entry.get("effective_date", "").strip(), # Date format validation in Validation module
                termination_date = entry.get("termination_date", "").strip(), # Date format validation in Validation module
                notional_amount = notional_amt,
                notional_currency = entry.get("notional_currency", "").strip().upper() if entry.get("notional_currency") is not None else None,
                price = price_val,
                price_currency = entry.get("price_currency", "").strip().upper() if entry.get("price_currency") is not None else None,
                # ... Map other fields based on CDE ...
                processing_status = "Processed" if not processing_errors else "ProcessedWithErrors", # Indicate if processing had issues
                processing_errors = processing_errors, # Store errors in DB
                original_raw_data_id = original_raw_db_id, # Link to raw data
                processing_timestamp = datetime.utcnow(),
                validation_status = "Pending" # Initial validation status
            )
            processed_data_list.append(db_processed_entry)

            # Prepare Pydantic model for the next module (Validation)
            # This converts the DB model data back to a Pydantic model format expected by Validation
            # Ensure all fields required by the Pydantic model are present
            pydantic_processed_entry = ProcessedSwapData(
                 unique_transaction_identifier = db_processed_entry.unique_transaction_identifier,
                 reporting_counterparty_lei = db_processed_entry.reporting_counterparty_lei,
                 other_counterparty_lei = db_processed_entry.other_counterparty_lei,
                 action_type = db_processed_entry.action_type,
                 event_type = db_processed_entry.event_type,
                 asset_class = db_processed_entry.asset_class,
                 effective_date = db_processed_entry.effective_date,
                 termination_date = db_processed_entry.termination_date,
                 notional_amount = db_processed_entry.notional_amount,
                 notional_currency = db_processed_entry.notional_currency,
                 price = db_processed_entry.price,
                 price_currency = db_processed_entry.price_currency,
                 processing_status = db_processed_entry.processing_status,
                 processing_errors = db_processed_entry.processing_errors,
                 original_raw_data_id = db_processed_entry.original_raw_data_id
            )
            data_for_validation.append(pydantic_processed_entry)


            # If processing errors occurred, mark this entry for reporting to error monitor
            if processing_errors:
                 processing_failed_for_reporting.append({
                     "source_module": "data-processing",
                     "data": pydantic_processed_entry.model_dump(), # Send the processed data payload
                     "errors": processing_errors
                 })


        except Exception as e:
            logger.error(f"Critical error processing entry with source ID {source_trade_id}: {e}", exc_info=True)
            critical_error_details = {
                "source_module": "data-processing",
                "source_data": entry, # Send original raw data for critical failures
                "errors": [f"Critical Processing Error: {e}"]
            }
            processing_failed_for_reporting.append(critical_error_details)
            send_alert("Critical", f"Critical error during data processing for source ID {source_trade_id}: {e}", critical_error_details)
            # TODO: Ensure critical failures are reported to error monitor even if forwarding to validation fails

    logger.info(f"Finished processing {len(data)} entries. Generated {len(processed_data_list)} processed entries with {len(processing_failed_for_reporting)} processing issues.")

    # Simulate storing processed data persistently in the database
    try:
        db.add_all(processed_data_list) # Add all records to the session
        db.commit() # Commit the transaction
        # Refresh records to get generated IDs if needed
        # for record in processed_data_list:
        #     db.refresh(record)
        logger.info(f"Successfully simulated storing {len(processed_data_list)} entries in processed_swap_data table.")

    except Exception as e:
        db.rollback() # Rollback the transaction in case of error
        logger.error(f"Failed to store processed data in database: {e}", exc_info=True)
        send_alert("Critical", f"Database error storing processed data: {e}", {"module": "data-processing", "error": str(e)})
        # If database storage fails, we cannot proceed.
        raise HTTPException(status_code=500, detail="Failed to store processed data")


    # Forward processed data (including those with processing_errors logged) to validation module
    # The validation module will perform comprehensive validation and handle errors further.
    if data_for_validation:
        logger.info(f"Forwarding {len(data_for_validation)} entries to validation module.")
        try:
            async with httpx.AsyncClient() as client:
                 # Use the URL from environment variables
                 # Convert Pydantic models to dicts for JSON payload
                 response = await client.post(VALIDATION_MODULE_URL, json=[entry.model_dump() for entry in data_for_validation], timeout=60.0) # Add timeout
                 response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
                 logger.info(f"Successfully sent {len(data_for_validation)} entries to validation module. Response: {response.json()}")
                 # TODO: Handle validation module response (e.g., check status)
                 # TODO: Update status in processed_swap_data table based on validation outcome (later)

        except httpx.RequestError as exc:
            logger.error(f"Failed to send data to validation module: {exc}", exc_info=True)
            send_alert("Error", f"Failed to forward data to validation module: {exc}", {"module": "data-processing", "error": str(exc), "target_url": VALIDATION_MODULE_URL})
            # TODO: Implement robust error handling: retry logic, Dead Letter Queue (DLQ), or mark data for later processing in DB

        except Exception as e:
             logger.error(f"An unexpected error occurred during validation module call: {e}", exc_info=True)
             send_alert("Critical", f"Unexpected error calling validation module: {e}", {"module": "data-processing", "error": str(e), "target_url": VALIDATION_MODULE_URL})
             # TODO: Implement robust error handling

    # Report entries that had processing failures to the error monitor
    if processing_failed_for_reporting:
        logger.error(f"Reporting {len(processing_failed_for_reporting)} processing failures to error monitor.")
        try:
            async with httpx.AsyncClient() as client:
                # Use the URL from environment variables
                response = await client.post(ERROR_MONITOR_MODULE_URL, json=processing_failed_for_reporting, timeout=30.0)
                response.raise_for_status()
                logger.info(f"Successfully reported processing failures to error monitor module. Response: {response.json()}")
        except httpx.RequestError as exc:
            logger.error(f"Failed to report processing failures to error monitor module: {exc}", exc_info=True)
            send_alert("Error", f"Failed to report processing failures to error monitor: {exc}", {"module": "data-processing", "error": str(exc), "target_url": ERROR_MONITOR_MODULE_URL})
            # TODO: Implement robust error handling for error reporting itself
        except Exception as e:
             logger.error(f"An unexpected error occurred during error monitor reporting: {e}", exc_info=True)
             send_alert("Critical", f"Unexpected error reporting processing failures: {e}", {"module": "data-processing", "error": str(e), "target_url": ERROR_MONITOR_MODULE_URL})


    return {"status": "success", "processed_count": len(processed_data_list), "processing_failed_count": len(processing_failed_for_reporting), "validation_forward_status": "attempted"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for the Data Processing module.
    Checks database connectivity.
    """
    try:
        # Attempt to query the database to check connectivity
        db.query(ProcessedSwapDataDB).limit(1).all()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
        logger.error(f"Database health check failed: {e}", exc_info=True)
        send_alert("Critical", f"Database connectivity issue in Data Processing: {e}", {"module": "data-processing", "check": "db_connectivity"})

    return {"status": "ok", "database_status": db_status}

# To run this module locally:
# 1. Ensure your database is running.
# 2. Set the DATABASE_URL environment variable if not using SQLite.
# 3. Set VALIDATION_MODULE_URL and ERROR_MONITOR_MODULE_URL env vars if not using defaults.
# 4. Run uvicorn: uvicorn main:app --reload --port 8001
