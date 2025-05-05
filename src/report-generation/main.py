# src/report-generation/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn
import httpx # Used for simulating HTTP calls between services
from datetime import datetime
import os # Simulate file creation

# src.common에서 로거, 임시 저장소, 유틸 함수 가져오기
from common.utils import logger, generated_reports_db, send_alert
# data-processing 모듈에서 정의한 모델 임포트 (실제로는 공유 모델 사용 또는 API 스펙 정의)
from data_processing.main import ProcessedSwapData

# TODO: Replace direct function calls with actual API calls or message queue publishing
# REPORT_SUBMISSION_MODULE_URL = "http://report-submission-service:80/" # Example in K8s
REPORT_SUBMISSION_MODULE_URL = "http://localhost:8004/submit-report" # Local testing URL (P2 module)

# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

# Simulate a directory for generated report files
REPORT_OUTPUT_DIR = "./generated_reports"
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True) # Create directory if it doesn't exist

@app.post("/generate-report")
async def generate_report(data: List[ProcessedSwapData]): # Receives Valid ProcessedSwapData from Validation (simulated)
    """
    API endpoint to generate regulatory report files from valid swap data.
    """
    logger.info(f"Received {len(data)} valid data entries for report generation.")

    if not data:
        logger.info("No valid data received for report generation.")
        return {"status": "success", "generated_count": 0, "submission_forward_status": "skipped (no data)"}

    generated_report_info_list = []
    report_generation_errors: List[Dict[str, Any]] = []

    # TODO: Implement actual report formatting logic based on SDR requirements (e.g., CFTC Part 43/45 XML/CSV)
    # This is a complex step involving mapping CDEs to the specific report format,
    # handling nuances like block trades, action types, etc.

    # For MVP, simulate creating a simple text file report per entry or batch
    report_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    batch_report_filename = f"swap_report_batch_{report_timestamp}_{uuid.uuid4().hex[:6]}.txt"
    batch_report_path = os.path.join(REPORT_OUTPUT_DIR, batch_report_filename)

    try:
        with open(batch_report_path, "w") as f:
            f.write(f"## Swap Report Batch - Generated at {datetime.now().isoformat()}\n")
            f.write(f"## Number of Entries: {len(data)}\n")
            f.write("----------------------------------------------------\n")

            for entry in data:
                uti = entry.unique_transaction_identifier
                try:
                    # Simulate formatting a single entry
                    report_line = f"UTI: {uti}, Action: {entry.action_type}, Asset Class: {entry.asset_class}, Notional: {entry.notional_amount} {entry.notional_currency}, Effective Date: {entry.effective_date}, Reporting LEI: {entry.reporting_counterparty_lei}\n"
                    f.write(report_line)
                    logger.debug(f"Formatted entry for report: {uti}")

                    # Store info about the generated report entry
                    generated_report_info_list.append({
                        "uti": uti,
                        "report_filename": batch_report_filename,
                        "generation_timestamp": datetime.now().isoformat(),
                        "status": "Generated"
                    })

                except Exception as e:
                    logger.error(f"Error formatting report entry for UTI {uti}: {e}", exc_info=True)
                    report_generation_errors.append({
                        "source_module": "report-generation",
                        "data": entry.model_dump(),
                        "errors": [f"Error formatting report entry: {e}"]
                    })
                    send_alert("Error", f"Error formatting report entry for UTI {uti}: {e}", {"module": "report-generation", "uti": uti, "error": str(e)})
                    # Continue processing other entries

            f.write("----------------------------------------------------\n")
            logger.info(f"Successfully generated batch report file: {batch_report_filename}")

    except Exception as e:
        logger.error(f"Critical error writing batch report file {batch_report_filename}: {e}", exc_info=True)
        send_alert("Critical", f"Critical error writing batch report file: {e}", {"module": "report-generation", "filename": batch_report_filename, "error": str(e)})
        # If file writing fails critically, none of the entries in this batch can be reported
        # TODO: Handle this critical failure - perhaps mark all entries in this batch as failed in DB

    # Simulate storing info about generated reports persistently
    # In a real system, this would link report entries to the generated file and submission status
    generated_reports_db.extend(generated_report_info_list)
    logger.info(f"Simulated storing {len(generated_report_info_list)} generated report entries info in generated_reports_db. Total: {len(generated_reports_db)}")


    # Report any formatting errors to the error monitor
    if report_generation_errors:
         logger.error(f"Reporting {len(report_generation_errors)} report generation errors to error monitor.")
         try:
             async with httpx.AsyncClient() as client:
                 response = await client.post(ERROR_MONITOR_MODULE_URL, json=report_generation_errors, timeout=30.0)
                 response.raise_for_status()
                 logger.info(f"Successfully reported report generation errors. Response: {response.json()}")
         except httpx.RequestError as exc:
             logger.error(f"Failed to report report generation errors to error monitor: {exc}", exc_info=True)
             send_alert("Error", f"Failed to report report generation errors: {exc}", {"module": "report-generation", "error": str(exc)})
         except Exception as e:
              logger.error(f"An unexpected error occurred during error monitor reporting: {e}", exc_info=True)
              send_alert("Critical", f"Unexpected error reporting report generation errors: {e}", {"module": "report-generation", "error": str(e)})


    # Forward the generated report file path/info to the Report Submission module
    if generated_report_info_list: # Only attempt submission if at least one entry was formatted
        logger.info(f"Forwarding generated report file info ({batch_report_filename}) to Report Submission.")
        try:
            async with httpx.AsyncClient() as client:
                # In a real system, you might send the file path, or the content itself, or a reference.
                # Sending file path requires shared storage or file transfer.
                # Sending content might be feasible for smaller reports.
                # Sending a reference to a shared location (S3, Azure Blob) is common.
                # For this simulation, we'll just send the file path.
                submission_payload = {
                    "report_filename": batch_report_filename,
                    "report_path": batch_report_path,
                    "entry_count": len(generated_report_info_list)
                }
                response = await client.post(REPORT_SUBMISSION_MODULE_URL, json=submission_payload, timeout=120.0) # Allow longer timeout for submission
                response.raise_for_status()
                logger.info(f"Successfully sent report info to report submission module. Response: {response.json()}")
                # TODO: Handle submission module response (e.g., update report status in DB to 'Submitted')

        except httpx.RequestError as exc:
            logger.error(f"Failed to send report info to report submission module: {exc}", exc_info=True)
            send_alert("Error", f"Failed to forward report to submission: {exc}", {"module": "report-generation", "filename": batch_report_filename, "error": str(exc)})
            # TODO: Implement robust error handling: retry, DLQ, or mark report for manual submission/re-generation
        except Exception as e:
             logger.error(f"An unexpected error occurred during report submission module call: {e}", exc_info=True)
             send_alert("Critical", f"Unexpected error calling report submission module: {e}", {"module": "report-generation", "filename": batch_report_filename, "error": str(e)})


    return {"status": "success", "generated_count": len(generated_report_info_list), "submission_forward_status": "attempted"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Report Generation module.
    """
    return {"status": "ok", "generated_report_entries_in_db": len(generated_reports_db)}

# To run this module locally:
# uvicorn main:app --reload --port 8003


#=================== 
# src/report-generation/main.py

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn
import httpx
import os # To read environment variables, simulate file creation
from datetime import datetime
import uuid # To generate unique IDs

# --- SQLAlchemy Imports ---
from sqlalchemy.orm import Session
from sqlalchemy import select # For selecting data

# src.common에서 로거, DB 설정 및 모델 가져오기
from common.utils import logger, get_db, GeneratedReport, ProcessedSwapDataDB, create_database_tables # Import DB models
from common.utils import send_alert # Import utility

# --- Ensure database tables are created on startup (for local dev) ---
# In production, handle migrations separately
# create_database_tables() # Already called in ingestion/error_monitoring, ensure it's run once

# TODO: Replace hardcoded URLs with Environment Variables injected by Kubernetes
# REPORT_SUBMISSION_MODULE_URL = os.environ.get("REPORT_SUBMISSION_MODULE_URL", "http://report-submission-service:80/submit-report") # Example in K8s
# ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://error-monitoring-service:80/report_error") # Example in K8s
REPORT_SUBMISSION_MODULE_URL = os.environ.get("REPORT_SUBMISSION_MODULE_URL", "http://localhost:8004/submit-report") # Default to Local testing URL (P2 module)
ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://localhost:8005/report_error") # Default to Local testing URL


# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

# Simulate a directory for generated report files (Local Placeholder)
# In a real system, this would be interaction with S3/Blob Storage SDK
REPORT_OUTPUT_DIR = os.environ.get("REPORT_OUTPUT_DIR", "./generated_reports_local")
os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True) # Create directory if it doesn't exist
logger.info(f"Using local directory for report generation simulation: {REPORT_OUTPUT_DIR}")

@app.post("/generate-report")
async def generate_report(data: List[Dict[str, Any]], db: Session = Depends(get_db)): # Receives Valid ProcessedSwapData as Dict from Validation
    """
    API endpoint to generate regulatory report files from valid swap data.
    Stores report info in the database and forwards to submission.
    """
    logger.info(f"Received {len(data)} valid data entries for report generation.")

    if not data:
        logger.info("No valid data received for report generation.")
        return {"status": "success", "generated_count": 0, "submission_forward_status": "skipped (no data)"}

    # --- Simulate Report File Generation (Local Placeholder) ---
    # In a real system, this would use a file storage SDK (S3, Blob)
    report_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    batch_report_filename = f"swap_report_batch_{report_timestamp}_{uuid.uuid4().hex[:6]}.txt" # Example filename
    batch_report_local_path = os.path.join(REPORT_OUTPUT_DIR, batch_report_filename)

    generated_report_info_list: List[GeneratedReport] = []
    report_generation_errors: List[Dict[str, Any]] = []

    try:
        # Simulate writing report content to a local file
        with open(batch_report_local_path, "w") as f:
            f.write(f"## Swap Report Batch - Generated at {datetime.now().isoformat()}\n")
            f.write(f"## Number of Entries: {len(data)}\n")
            f.write("----------------------------------------------------\n")

            for entry_dict in data: # Data is received as list of dicts
                uti = entry_dict.get("unique_transaction_identifier", "N/A")
                try:
                    # Simulate formatting a single entry based on the dict data
                    # This is where you'd map dict fields to the specific report format (XML, CSV)
                    report_line = f"UTI: {uti}, Action: {entry_dict.get('action_type')}, Asset Class: {entry_dict.get('asset_class')}, Notional: {entry_dict.get('notional_amount')} {entry_dict.get('notional_currency')}, Effective Date: {entry_dict.get('effective_date')}, Reporting LEI: {entry_dict.get('reporting_counterparty_lei')}\n"
                    f.write(report_line)
                    logger.debug(f"Formatted entry for report: {uti}")

                    # Create DB record for this generated report entry
                    # Note: A single GeneratedReport record might represent a batch file,
                    # or you might have a separate table linking UTIs to batch files.
                    # Let's create one GeneratedReport record per batch file for simplicity here.
                    # If you need to track each UTI's report status, link ProcessedSwapDataDB to GeneratedReport.

                except Exception as e:
                    logger.error(f"Error formatting report entry for UTI {uti}: {e}", exc_info=True)
                    # Find the original processed data record in DB to link the error? Or just use the dict?
                    # Using the dict payload for error reporting for simplicity.
                    report_generation_errors.append({
                        "source_module": "report-generation",
                        "data": entry_dict, # Include the data that failed formatting
                        "errors": [f"Error formatting report entry: {e}"]
                    })
                    send_alert("Error", f"Error formatting report entry for UTI {uti}: {e}", {"module": "report-generation", "uti": uti, "error": str(e)})
                    # Continue processing other entries

            f.write("----------------------------------------------------\n")
            logger.info(f"Successfully simulated writing batch report file: {batch_report_local_path}")

        # Create the main GeneratedReport DB record for the batch file
        db_generated_report = GeneratedReport(
            report_filename=batch_report_filename,
            report_storage_path=batch_report_local_path, # Store local path for simulation
            entry_count=len(data) - len(report_generation_errors), # Count entries successfully formatted
            generation_timestamp=datetime.utcnow(),
            status="Generated"
        )
        generated_report_info_list.append(db_generated_report)


    except Exception as e:
        logger.error(f"Critical error creating/writing batch report file {batch_report_local_path}: {e}", exc_info=True)
        send_alert("Critical", f"Critical error writing batch report file: {e}", {"module": "report-generation", "filename": batch_report_filename, "error": str(e)})
        # If file writing fails critically, none of the entries in this batch can be reported
        # TODO: Handle this critical failure - perhaps mark all entries in this batch as failed in DB
        raise HTTPException(status_code=500, detail=f"Failed to generate report file: {e}")


    # Simulate storing info about generated reports persistently in the database
    try:
        db.add_all(generated_report_info_list)
        db.commit()
        # Refresh to get the generated ID for the report record
        db.refresh(db_generated_report)
        logger.info(f"Successfully simulated storing {len(generated_report_info_list)} generated report records in generated_reports table. Total: {db.query(GeneratedReport).count()}")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store generated report info in database: {e}", exc_info=True)
        send_alert("Critical", f"Database error storing generated report info: {e}", {"module": "report-generation", "error": str(e)})
        # If DB storage fails, we cannot reliably track this report.
        # TODO: Decide how to handle this - maybe delete the generated file?

        # If DB storage fails, we cannot proceed to submission reliably.
        raise HTTPException(status_code=500, detail="Failed to store generated report info")


    # Report any formatting errors to the error monitor
    if report_generation_errors:
         logger.error(f"Reporting {len(report_generation_errors)} report generation errors to error monitor.")
         try:
             async with httpx.AsyncClient() as client:
                 # Use the URL from environment variables
                 response = await client.post(ERROR_MONITOR_MODULE_URL, json=report_generation_errors, timeout=30.0)
                 response.raise_for_status()
                 logger.info(f"Successfully reported report generation errors. Response: {response.json()}")
         except httpx.RequestError as exc:
             logger.error(f"Failed to report report generation errors to error monitor: {exc}", exc_info=True)
             send_alert("Error", f"Failed to report report generation errors: {exc}", {"module": "report-generation", "error": str(exc), "target_url": ERROR_MONITOR_MODULE_URL})
             # TODO: Implement robust error handling for error reporting itself
         except Exception as e:
              logger.error(f"An unexpected error occurred during error monitor reporting: {e}", exc_info=True)
              send_alert("Critical", f"Unexpected error reporting report generation errors: {e}", {"module": "report-generation", "error": str(e), "target_url": ERROR_MONITOR_MODULE_URL})


    # Forward the generated report file info (including DB ID) to the Report Submission module
    if generated_report_info_list: # Only attempt submission if at least one report record was created
        logger.info(f"Forwarding generated report info (DB ID: {db_generated_report.id}, Filename: {db_generated_report.report_filename}) to Report Submission.")
        try:
            async with httpx.AsyncClient() as client:
                # Send the DB record ID and relevant info to the submission module
                submission_payload = {
                    "report_id": db_generated_report.id, # Pass the DB ID
                    "report_filename": db_generated_report.report_filename,
                    "report_storage_path": db_generated_report.report_storage_path, # Pass the storage path/identifier
                    "entry_count": db_generated_report.entry_count
                }
                # Use the URL from environment variables
                response = await client.post(REPORT_SUBMISSION_MODULE_URL, json=submission_payload, timeout=120.0) # Allow longer timeout for submission
                response.raise_for_status()
                logger.info(f"Successfully sent report info to report submission module. Response: {response.json()}")
                # TODO: Handle submission module response (e.g., update report status in DB to 'Submitted' or 'SubmissionFailed')
                # A better approach is for the submission module to update the status directly or via a callback.

        except httpx.RequestError as exc:
            logger.error(f"Failed to send report info to report submission module: {exc}", exc_info=True)
            send_alert("Error", f"Failed to forward report to submission: {exc}", {"module": "report-generation", "report_id": db_generated_report.id, "error": str(exc), "target_url": REPORT_SUBMISSION_MODULE_URL})
            # TODO: Implement robust error handling: retry, DLQ, or mark report for manual submission/re-generation
            # TODO: Update report status in DB to 'SubmissionFailed'

        except Exception as e:
             logger.error(f"An unexpected error occurred during report submission module call: {e}", exc_info=True)
             send_alert("Critical", f"Unexpected error calling report submission module: {e}", {"module": "report-generation", "report_id": db_generated_report.id, "error": str(e), "target_url": REPORT_SUBMISSION_MODULE_URL})
             # TODO: Implement robust error handling
             # TODO: Update report status in DB to 'SubmissionFailed'


    return {"status": "success", "generated_count": len(generated_report_info_list), "submission_forward_status": "attempted"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for the Report Generation module.
    Checks database connectivity and local report directory access.
    """
    db_status = "ok"
    try:
        # Attempt to query the database to check connectivity
        db.query(GeneratedReport).limit(1).all()
        db.query(ProcessedSwapDataDB).limit(1).all() # Also check processed data table
    except Exception as e:
        db_status = f"error: {e}"
        logger.error(f"Database health check failed: {e}", exc_info=True)
        send_alert("Critical", f"Database connectivity issue in Report Generation: {e}", {"module": "report-generation", "check": "db_connectivity"})

    file_storage_status = "ok"
    try:
        # Check if the local report directory is writable (simulating file storage access)
        test_file = os.path.join(REPORT_OUTPUT_DIR, ".test_write")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        file_storage_status = f"error: {e}"
        logger.error(f"File storage (local dir) access check failed: {e}", exc_info=True)
        send_alert("Critical", f"File storage access issue in Report Generation: {e}", {"module": "report-generation", "check": "file_storage_access"})


    return {"status": "ok", "database_status": db_status, "file_storage_status": file_storage_status}

# To run this module locally:
# 1. Ensure your database is running.
# 2. Set the DATABASE_URL environment variable if not using SQLite.
# 3. Set REPORT_SUBMISSION_MODULE_URL and ERROR_MONITOR_MODULE_URL env vars if not using defaults.
# 4. Set REPORT_OUTPUT_DIR env var if not using default local path.
# 5. Run uvicorn: uvicorn main:app --reload --port 8003
