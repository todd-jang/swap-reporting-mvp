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
