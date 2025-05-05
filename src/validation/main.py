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
