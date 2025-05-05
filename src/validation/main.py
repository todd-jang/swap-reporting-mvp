# src/validation/main.py

from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn
# import httpx # 실제 HTTP 호출 시 사용
from datetime import datetime

# src.common에서 로거, 임시 저장소, 유틸 함수 가져오기
from common.utils import logger, validation_results_store, invalid_data_store, validate_lei
# data-processing 모듈에서 정의한 모델 임포트 (실제로는 공유 모델 사용 또는 API 스펙 정의)
from data_processing.main import ProcessedSwapData

# TODO: Replace direct function calls with actual API calls or message queue publishing
from error_monitoring.main import report_error as call_error_monitor_module
# TODO: Import/Call Report Generation module (P2)

# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/validate")
async def validate_swap_data(data: List[ProcessedSwapData]): # Receives ProcessedSwapData model from Processing module (simulated)
    """
    API endpoint to validate processed swap trade data against regulatory rules.
    Separates valid and invalid data and forwards invalid data to the error monitor.
    """
    logger.info(f"Received {len(data)} data entries for validation from Processing.")

    validation_results = []
    invalid_entries_for_reporting: List[Dict[str, Any]] = [] # Data and errors to send to error monitor
    valid_entries: List[ProcessedSwapData] = [] # Data that passed validation

    for entry in data:
        trade_id = entry.unique_transaction_identifier
        is_valid = True
        errors: List[str] = [] # List to store validation error messages

        logger.info(f"Validating entry with UTI: {trade_id}")

        # --- Core Validation Logic (Based on CFTC Part 45/43 and CDE examples) ---
        # Implement comprehensive validation rules here.

        # Rule 1: Check if Processing had critical errors
        if entry.processing_errors:
             is_valid = False
             errors.extend([f"Processing Error: {err}" for err in entry.processing_errors])
             logger.warning(f"Validation failed for UTI {trade_id} due to processing errors: {entry.processing_errors}")


        # Rule 2: Check if Notional Amount is positive and valid
        if entry.notional_amount is None or entry.notional_amount <= 0:
            is_valid = False
            errors.append("Notional Amount must be a positive value.")
            logger.warning(f"Validation failed for UTI {trade_id}: Notional Amount is not positive or missing.")

        # Rule 3: Check if required Date fields are present and in valid format (YYYY-MM-DD)
        try:
            datetime.strptime(entry.effective_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            is_valid = False
            errors.append(f"Effective Date '{entry.effective_date}' is missing or invalid format (YYYY-MM-DD).")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Effective Date.")

        try:
            datetime.strptime(entry.termination_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            is_valid = False
            errors.append(f"Termination Date '{entry.termination_date}' is missing or invalid format (YYYY-MM-DD).")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Termination Date.")

        # Rule 4: Check if Effective Date is before or equal to Termination Date
        if is_valid and entry.effective_date and entry.termination_date: # Only check if dates are valid format
            try:
                eff_date = datetime.strptime(entry.effective_date, '%Y-%m-%d')
                term_date = datetime.strptime(entry.termination_date, '%Y-%m-%d')
                if eff_date > term_date:
                     is_valid = False
                     errors.append("Effective Date must be before or equal to Termination Date.")
                     logger.warning(f"Validation failed for UTI {trade_id}: Effective Date after Termination Date.")
            except Exception:
                 # Should not happen if previous date format checks passed, but for safety
                 pass


        # Rule 5: Check LEI format validity (using common utility)
        # Note: Basic format checked in processing, but re-checked here for robustness
        if not validate_lei(entry.reporting_counterparty_lei):
            is_valid = False
            errors.append(f"Reporting Counterparty LEI '{entry.reporting_counterparty_lei}' has invalid format.")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Reporting Counterparty LEI format.")

        if not validate_lei(entry.other_counterparty_lei):
            is_valid = False
            errors.append(f"Other Counterparty LEI '{entry.other_counterparty_lei}' has invalid format.")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Other Counterparty LEI format.")

        # TODO: Add many more validation rules based on specific regulations (Part 45/43, CDE)
        # - Asset class specific rules
        # - Conditional field requirements
        # - Consistency checks across related fields
        # - LEI status check (Active) - might require external lookup

        # --- End of Validation Rules ---

        validation_results.append({
            "unique_transaction_identifier": trade_id,
            "is_valid": is_valid,
            "errors": errors,
            "data": entry.model_dump() # Include the data that was validated
        })

        if not is_valid:
            invalid_entries_for_reporting.append({"data": entry.model_dump(), "errors": errors})
        else:
            valid_entries.append(entry)

    logger.info(f"Finished validation for {len(data)} entries. Found {len(invalid_entries_for_reporting)} invalid entries.")

    # Store validation results (including valid and invalid)
    validation_results_store.extend(validation_results)
    logger.info(f"Stored {len(validation_results)} validation results. Total: {len(validation_results_store)}")

    # Forward invalid entries to the error management module
    if invalid_entries_for_reporting:
        logger.info(f"Reporting {len(invalid_entries_for_reporting)} invalid entries to error monitor.")
        try:
            # Simulate calling the error monitor module function directly
            # Replace with: await client.post(ERROR_MONITOR_MODULE_URL, json=invalid_entries_for_reporting)
            error_monitor_response = await call_error_monitor_module(invalid_entries_for_reporting)
            logger.info(f"Error monitor module responded: {error_monitor_response}")
        except Exception as e:
            logger.error(f"Failed to report invalid entries to error monitor: {e}", exc_info=True)


    # Forward valid entries to the next stage (Report Generation - P2)
    if valid_entries:
         logger.info(f"Passing {len(valid_entries)} valid entries to the next stage (Report Generation - TBD).")
         # TODO: Call Report Generation module API or send to its message queue
         # Example: await call_report_generation_module(valid_entries)


    return {"status": "success", "validated_count": len(data), "invalid_count": len(invalid_entries_for_reporting), "valid_count": len(valid_entries)}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Validation module.
    """
    return {"status": "ok", "validation_results_count_in_store": len(validation_results_store), "invalid_data_count_in_store": len(invalid_data_store)}

# To run this module locally:
# uvicorn main:app --reload --port 8002


#================= process of replacing the simulated components with real-world technologies
# src/validation/main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn
import httpx
import os # To read environment variables
from datetime import datetime

# --- SQLAlchemy Imports ---
from sqlalchemy.orm import Session
from sqlalchemy import select # For selecting data

# src.common에서 로거, DB 설정 및 모델 가져오기
from common.utils import logger, get_db, ValidationResult, ProcessedSwapDataDB, create_database_tables # Import DB models
from common.utils import validate_lei, send_alert # Import utilities
# data-processing 모듈에서 정의한 모델 임포트 (실제로는 공유 모델 사용 또는 API 스펙 정의)
from data_processing.main import ProcessedSwapData # Pydantic model for input

# --- Ensure database tables are created on startup (for local dev) ---
# In production, handle migrations separately
# create_database_tables() # Already called in ingestion/error_monitoring, ensure it's run once

# TODO: Replace hardcoded URLs with Environment Variables injected by Kubernetes
# ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://error-monitoring-service:80/report_error") # Example in K8s
# REPORT_GENERATION_MODULE_URL = os.environ.get("REPORT_GENERATION_MODULE_URL", "http://report-generation-service:80/generate-report") # Example in K8s
ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://localhost:8005/report_error") # Default to Local testing URL
REPORT_GENERATION_MODULE_URL = os.environ.get("REPORT_GENERATION_MODULE_URL", "http://localhost:8003/generate-report") # Default to Local testing URL (P2 module)


# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/validate")
async def validate_swap_data(data: List[ProcessedSwapData], db: Session = Depends(get_db)): # Receives ProcessedSwapData model from Processing module
    """
    API endpoint to validate processed swap trade data against regulatory rules.
    Performs validation, stores results in the database, and forwards valid data
    to report generation and invalid data to error monitor.
    """
    logger.info(f"Received {len(data)} data entries for validation from Processing.")

    validation_results_list: List[ValidationResult] = [] # SQLAlchemy models for DB
    invalid_entries_for_reporting: List[Dict[str, Any]] = [] # Data and errors to send to error monitor
    valid_entries: List[ProcessedSwapData] = [] # Data that passed validation, for next module

    for entry in data:
        trade_id = entry.unique_transaction_identifier
        is_valid = True
        errors: List[str] = [] # List to store validation error messages

        logger.info(f"Validating entry with UTI: {trade_id}")

        # --- Core Validation Logic (Based on CFTC Part 45/43 and CDE examples) ---
        # Implement comprehensive validation rules here. Refer to the CFTC document.

        # Rule 1: Check if Processing had critical errors (already reported, but mark as invalid here)
        if entry.processing_errors:
             is_valid = False
             errors.extend([f"Processing Error: {err}" for err in entry.processing_errors])
             logger.warning(f"Validation failed for UTI {trade_id} due to processing errors.") # Already logged in processing, but useful here


        # Rule 2: Check if Notional Amount is positive and valid (re-check after processing)
        if entry.notional_amount is None or entry.notional_amount <= 0:
            is_valid = False
            errors.append("Notional Amount must be a positive value.")
            logger.warning(f"Validation failed for UTI {trade_id}: Notional Amount is not positive or missing.")

        # Rule 3: Check if required Date fields are present and in valid format (YYYY-MM-DD)
        try:
            datetime.strptime(entry.effective_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            is_valid = False
            errors.append(f"Effective Date '{entry.effective_date}' is missing or invalid format (YYYY-MM-DD).")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Effective Date.")

        try:
            datetime.strptime(entry.termination_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            is_valid = False
            errors.append(f"Termination Date '{entry.termination_date}' is missing or invalid format (YYYY-MM-DD).")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Termination Date.")

        # Rule 4: Check if Effective Date is before or equal to Termination Date
        if is_valid and entry.effective_date and entry.termination_date: # Only check if dates are valid format based on Rule 3
            try:
                eff_date = datetime.strptime(entry.effective_date, '%Y-%m-%d')
                term_date = datetime.strptime(entry.termination_date, '%Y-%m-%d')
                if eff_date > term_date:
                     is_valid = False
                     errors.append("Effective Date must be before or equal to Termination Date.")
                     logger.warning(f"Validation failed for UTI {trade_id}: Effective Date after Termination Date.")
            except Exception as e:
                 # Should not happen if previous date format checks passed, but for safety
                 logger.error(f"Unexpected error during date comparison for UTI {trade_id}: {e}", exc_info=True)
                 is_valid = False # Treat as invalid if comparison fails unexpectedly
                 errors.append(f"Internal error comparing dates: {e}")
                 send_alert("Error", f"Internal error during date comparison for UTI {trade_id}", {"module": "validation", "uti": trade_id, "error": str(e)})


        # Rule 5: Check LEI format validity (using common utility) - Re-check
        if not validate_lei(entry.reporting_counterparty_lei):
            is_valid = False
            errors.append(f"Reporting Counterparty LEI '{entry.reporting_counterparty_lei}' has invalid format.")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Reporting Counterparty LEI format.")

        if not validate_lei(entry.other_counterparty_lei):
            is_valid = False
            errors.append(f"Other Counterparty LEI '{entry.other_counterparty_lei}' has invalid format.")
            logger.warning(f"Validation failed for UTI {trade_id}: Invalid Other Counterparty LEI format.")

        # Rule 6: Check if required LEIs are present for Action Type NEWT (New Trade)
        if entry.action_type == "NEWT":
            if not entry.reporting_counterparty_lei:
                 is_valid = False
                 errors.append("Reporting Counterparty LEI is required for NEWT action.")
                 logger.warning(f"Validation failed for UTI {trade_id}: Reporting LEI missing for NEWT.")
            if not entry.other_counterparty_lei:
                 is_valid = False
                 errors.append("Other Counterparty LEI is required for NEWT action.")
                 logger.warning(f"Validation failed for UTI {trade_id}: Other LEI missing for NEWT.")

        # TODO: Add many more validation rules based on specific regulations (Part 45/43, CDE)
        # - Asset class specific rules (e.g., IRS requires specific rate fields)
        # - Conditional field requirements based on Action Type or Event Type
        # - Consistency checks across related fields (e.g., Price Currency must match Notional Currency if applicable)
        # - LEI status check (Active) - might require external lookup (P2/P3 feature)
        # - Collateral/Margin fields validation (refer to document snippets)
        #   - Check presence and format of variation_margin_collected, currency_of_variation_margin_collected etc. (Pages 60-61)

        # --- End of Validation Rules ---

        # Find the corresponding processed data record in the DB to link the validation result
        # This assumes the processed data is already committed to the DB by the processing module
        processed_record = db.query(ProcessedSwapDataDB).filter(ProcessedSwapDataDB.unique_transaction_identifier == trade_id).first()
        processed_data_db_id = processed_record.id if processed_record else None
        if processed_record:
             # Update the validation_status in the processed data record
             processed_record.validation_status = "Valid" if is_valid else "Invalid"
             db.add(processed_record) # Stage the update


        # Create SQLAlchemy DB model instance for validation result
        db_validation_result = ValidationResult(
            unique_transaction_identifier = trade_id,
            is_valid = is_valid,
            errors = errors,
            validation_timestamp = datetime.utcnow(),
            processed_data_id = processed_data_db_id # Link to the processed data record
        )
        validation_results_list.append(db_validation_result)


        if not is_valid:
            # Prepare data for error reporting
            invalid_entries_for_reporting.append({
                "source_module": "validation",
                "data": entry.model_dump(), # Send the processed data payload
                "errors": errors
            })
            send_alert("Warning" if not entry.processing_errors else "Error", # Escalate if processing errors were present
                       f"Validation failed for UTI {trade_id}. Errors: {', '.join(errors)}",
                       {"module": "validation", "uti": trade_id, "errors": errors})
        else:
            valid_entries.append(entry)

    logger.info(f"Finished validation for {len(data)} entries. Found {len(invalid_entries_for_reporting)} invalid entries.")

    # Simulate storing validation results persistently in the database
    try:
        db.add_all(validation_results_list) # Add all new validation results
        db.commit() # Commit new validation results AND updates to processed_swap_data
        logger.info(f"Successfully simulated storing {len(validation_results_list)} validation results and updating processed data status in DB.")

    except Exception as e:
        db.rollback() # Rollback the transaction in case of error
        logger.error(f"Failed to store validation results or update processed data status in database: {e}", exc_info=True)
        send_alert("Critical", f"Database error storing validation results: {e}", {"module": "validation", "error": str(e)})
        # If database storage fails, we cannot proceed reliably.
        raise HTTPException(status_code=500, detail="Failed to store validation results")


    # Forward invalid entries to the error management module
    if invalid_entries_for_reporting:
        logger.info(f"Reporting {len(invalid_entries_for_reporting)} invalid entries to error monitor.")
        try:
            async with httpx.AsyncClient() as client:
                # Use the URL from environment variables
                response = await client.post(ERROR_MONITOR_MODULE_URL, json=invalid_entries_for_reporting, timeout=30.0)
                response.raise_for_status()
                logger.info(f"Successfully reported validation failures to error monitor module. Response: {response.json()}")
        except httpx.RequestError as exc:
            logger.error(f"Failed to report validation failures to error monitor module: {exc}", exc_info=True)
            send_alert("Error", f"Failed to report validation failures to error monitor: {exc}", {"module": "validation", "error": str(exc), "target_url": ERROR_MONITOR_MODULE_URL})
            # TODO: Implement robust error handling for error reporting itself
        except Exception as e:
             logger.error(f"An unexpected error occurred during error monitor reporting: {e}", exc_info=True)
             send_alert("Critical", f"Unexpected error reporting validation failures: {e}", {"module": "validation", "error": str(e), "target_url": ERROR_MONITOR_MODULE_URL})


    # Forward valid entries to the next stage (Report Generation - P2)
    if valid_entries:
         logger.info(f"Passing {len(valid_entries)} valid entries to the next stage (Report Generation).")
         try:
             async with httpx.AsyncClient() as client:
                 # Use the URL from environment variables
                 # Convert Pydantic models to dicts for JSON payload
                 response = await client.post(REPORT_GENERATION_MODULE_URL, json=[entry.model_dump() for entry in valid_entries], timeout=60.0)
                 response.raise_for_status()
                 logger.info(f"Successfully sent {len(valid_entries)} valid entries to report generation module. Response: {response.json()}")
                 # TODO: Handle report generation module response

         except httpx.RequestError as exc:
             logger.error(f"Failed to send valid data to report generation module: {exc}", exc_info=True)
             send_alert("Error", f"Failed to forward valid data to report generation: {exc}", {"module": "validation", "error": str(exc), "target_url": REPORT_GENERATION_MODULE_URL})
             # TODO: Implement robust error handling: retry, DLQ, or mark data for later processing
         except Exception as e:
             logger.error(f"An unexpected error occurred during report generation module call: {e}", exc_info=True)
             send_alert("Critical", f"Unexpected error calling report generation module: {e}", {"module": "validation", "error": str(e), "target_url": REPORT_GENERATION_MODULE_URL})
             # TODO: Implement robust error handling


    return {"status": "success", "validated_count": len(data), "invalid_count": len(invalid_entries_for_reporting), "valid_count": len(valid_entries), "report_generation_forward_status": "attempted"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for the Validation module.
    Checks database connectivity.
    """
    try:
        # Attempt to query the database to check connectivity
        db.query(ValidationResult).limit(1).all()
        db.query(ProcessedSwapDataDB).limit(1).all() # Also check processed data table
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
        logger.error(f"Database health check failed: {e}", exc_info=True)
        send_alert("Critical", f"Database connectivity issue in Validation: {e}", {"module": "validation", "check": "db_connectivity"})

    return {"status": "ok", "database_status": db_status}

# To run this module locally:
# 1. Ensure your database is running.
# 2. Set the DATABASE_URL environment variable if not using SQLite.
# 3. Set ERROR_MONITOR_MODULE_URL and REPORT_GENERATION_MODULE_URL env vars if not using defaults.
# 4. Run uvicorn: uvicorn main:app --reload --port 8002
