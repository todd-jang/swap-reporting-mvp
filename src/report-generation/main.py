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
