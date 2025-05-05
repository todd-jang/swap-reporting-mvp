# src/report-submission/main.py

from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn
import httpx # Used for simulating HTTP calls to SDR (external)
from datetime import datetime
import os # Simulate file reading/transfer

# src.common에서 로거, 임시 저장소, 유틸 함수 가져오기
from common.utils import logger, submission_history_db, send_alert

# TODO: Replace with actual SDR API Endpoint or SFTP details
# SDR_SUBMISSION_URL = "https://sdr.example.com/api/submit" # Example SDR API
# SDR_SFTP_HOST = "sftp.sdr.example.com" # Example SDR SFTP
# SDR_SFTP_USER = "your_sdr_user"
# SDR_SFTP_PASSWORD = "your_sdr_password" # Use secrets management in real system

# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/submit-report")
async def submit_report(report_info: Dict[str, Any]): # Receives report info from Report Generation (simulated)
    """
    API endpoint to submit generated report files to the SDR.
    """
    report_filename = report_info.get("report_filename")
    report_path = report_info.get("report_path")
    entry_count = report_info.get("entry_count", 0)

    if not report_path or not os.path.exists(report_path):
        logger.error(f"Report file not found for submission: {report_path}")
        send_alert("Error", f"Report file not found for submission: {report_path}", {"module": "report-submission", "report_path": report_path})
        raise HTTPException(status_code=400, detail=f"Report file not found: {report_path}")

    logger.info(f"Received request to submit report file: {report_filename} ({entry_count} entries)")

    submission_record = {
        "submission_id": str(uuid.uuid4()), # Unique ID for this submission attempt
        "report_filename": report_filename,
        "report_path": report_path,
        "entry_count": entry_count,
        "submission_timestamp": datetime.now().isoformat(),
        "status": "Pending", # Initial status
        "sdr_response": None,
        "error_details": None
    }

    # Simulate storing submission attempt persistently
    submission_history_db.append(submission_record)
    logger.info(f"Simulated storing submission record {submission_record['submission_id']} in submission_history_db.")


    # --- TODO: Implement actual SDR submission logic ---
    # This is the critical external integration point.
    # Options:
    # 1. HTTP POST to SDR API: Read file content and send as payload.
    # 2. SFTP File Transfer: Connect to SDR SFTP server and upload the file.
    # 3. Cloud Storage Integration: If SDR pulls from S3/Blob, move file there.

    submission_successful = False
    sdr_response_data = None
    submission_error = None

    try:
        # --- Simulate SDR Submission (using HTTP POST as example) ---
        # In a real scenario, replace this with actual SDR API call or SFTP logic.
        # This requires reading the file content.
        with open(report_path, "rb") as f: # Read in binary mode
            report_content = f.read()

        # Simulate sending the file content to a dummy endpoint or SDR API
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(SDR_SUBMISSION_URL, content=report_content, timeout=300.0) # Allow long timeout
        #     response.raise_for_status() # Raise for bad status codes
        #     sdr_response_data = response.json() # Assuming SDR returns JSON response
        #     submission_successful = True # Assume success if no exception and status is good

        # --- Simple Simulation: Assume success for now ---
        logger.info(f"Simulating successful submission of {report_filename} to SDR.")
        submission_successful = True
        sdr_response_data = {"status": "Accepted", "sdr_ack_id": f"ACK_{uuid.uuid4().hex[:8]}"}
        # --- End Simulation ---


    except httpx.RequestError as exc:
        submission_error = f"HTTP Submission Failed: {exc}"
        logger.error(f"HTTP submission failed for {report_filename}: {exc}", exc_info=True)
        send_alert("Error", f"SDR HTTP submission failed for {report_filename}: {exc}", {"module": "report-submission", "filename": report_filename, "error": str(exc)})
    except FileNotFoundError:
         submission_error = f"Report file not found during submission attempt: {report_path}"
         logger.error(f"Report file not found during submission attempt: {report_path}", exc_info=True)
         send_alert("Critical", f"Report file disappeared before submission: {report_path}", {"module": "report-submission", "report_path": report_path})
    except Exception as e:
        submission_error = f"Unexpected Submission Error: {e}"
        logger.error(f"An unexpected error occurred during submission of {report_filename}: {e}", exc_info=True)
        send_alert("Critical", f"Unexpected error during SDR submission: {e}", {"module": "report-submission", "filename": report_filename, "error": str(e)})


    # --- Update Submission Record Status ---
    for record in submission_history_db:
        if record["submission_id"] == submission_record["submission_id"]:
            if submission_successful:
                record["status"] = "Submitted"
                record["sdr_response"] = sdr_response_data
                logger.info(f"Submission {record['submission_id']} marked as Submitted.")
                # TODO: Trigger next step: SDR acknowledgement processing (P3/later)
                # SDR might send an acknowledgement file/message later.
            else:
                record["status"] = "Failed"
                record["error_details"] = submission_error
                logger.error(f"Submission {record['submission_id']} marked as Failed.")
                # TODO: Trigger error reporting to Error Monitoring module
                # TODO: Implement retry logic for failed submissions

            break # Found and updated the record

    if submission_successful:
        return {"status": "success", "submission_id": submission_record["submission_id"], "sdr_response": sdr_response_data}
    else:
        # If submission failed, report it as an error
        error_details_for_reporting = {
            "source_module": "report-submission",
            "data": report_info, # Include info about the report that failed to submit
            "errors": [submission_error]
        }
        logger.error(f"Reporting submission failure for {report_filename} to error monitor.")
        try:
            async with httpx.AsyncClient() as client:
                # Using client.post for demonstration. MQ is better.
                response = await client.post(ERROR_MONITOR_MODULE_URL, json=[error_details_for_reporting], timeout=30.0)
                response.raise_for_status()
                logger.info(f"Successfully reported submission failure to error monitor module. Response: {response.json()}")
        except httpx.RequestError as exc:
            logger.error(f"Failed to report submission failure to error monitor: {exc}", exc_info=True)
        except Exception as e:
             logger.error(f"An unexpected error occurred during error monitor reporting: {e}", exc_info=True)


        raise HTTPException(status_code=500, detail=f"Report submission failed: {submission_error}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Report Submission module.
    """
    return {"status": "ok", "submission_records_in_db": len(submission_history_db)}

# To run this module locally:
# uvicorn main:app --reload --port 8004
