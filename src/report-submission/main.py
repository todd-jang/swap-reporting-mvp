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

#=================

# src/report-submission/main.py

from fastapi import FastAPI, HTTPException, Depends, Query # Import Query for the new endpoint
from typing import List, Dict, Any, Optional
import uvicorn
import httpx # Used for simulating HTTP calls to SDR (external)
from datetime import datetime
import os # Simulate file reading/transfer
import uuid # To generate unique IDs

# --- SQLAlchemy Imports ---
from sqlalchemy.orm import Session
from sqlalchemy import select, desc # For selecting data and ordering

# src.common에서 로거, DB 설정 및 모델 가져오기
from common.utils import logger, get_db, SubmissionHistory, GeneratedReport, create_database_tables # Import DB models
from common.utils import send_alert # Import utility

# --- Ensure database tables are created on startup (for local dev) ---
# In production, handle migrations separately
# create_database_tables() # Already called in ingestion/error_monitoring, ensure it's run once

# TODO: Replace with actual SDR API Endpoint or SFTP details (using Environment Variables)
# SDR_SUBMISSION_URL = os.environ.get("SDR_SUBMISSION_URL", "https://sdr.example.com/api/submit") # Example SDR API
# SDR_SFTP_HOST = os.environ.get("SDR_SFTP_HOST", "sftp.sdr.example.com") # Example SDR SFTP
# SDR_SFTP_USER = os.environ.get("SDR_SFTP_USER", "your_sdr_user")
# SDR_SFTP_PASSWORD = os.environ.get("SDR_SFTP_PASSWORD", "your_sdr_password") # Use secrets management!
# ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://error-monitoring-service:80/report_error") # Example in K8s
ERROR_MONITOR_MODULE_URL = os.environ.get("ERROR_MONITOR_MODULE_URL", "http://localhost:8005/report_error") # Default to Local testing URL


# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/submit-report")
async def submit_report(report_info: Dict[str, Any], db: Session = Depends(get_db)): # Receives report info from Report Generation
    """
    API endpoint to submit generated report files to the SDR.
    Retrieves report info from the database and updates submission history.
    """
    report_id = report_info.get("report_id") # Get the DB ID of the generated report record

    if not report_id:
        logger.error(f"Missing report_id in submission request: {report_info}")
        send_alert("Error", "Missing report ID for submission", {"module": "report-submission", "report_info": report_info})
        raise HTTPException(status_code=400, detail="Missing required report ID")

    logger.info(f"Received request to submit report (Report DB ID: {report_id})")

    # Retrieve the generated report record from the database
    generated_report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
    if not generated_report:
         logger.error(f"Generated report record not found in DB for submission: {report_id}")
         send_alert("Error", f"Generated report record not found for submission: {report_id}", {"module": "report-submission", "report_id": report_id})
         raise HTTPException(status_code=404, detail=f"Generated report record not found: {report_id}")

    # Check if the report is already submitted or in progress
    if generated_report.status in ["Submitted", "SubmissionInProgress", "SDR_Accepted", "SDR_Rejected"]:
        logger.warning(f"Report {report_id} is already in status {generated_report.status}. Skipping submission.")
        return {"status": "skipped", "message": f"Report already in status {generated_report.status}", "report_id": report_id}


    # Create a submission history record in the database
    db_submission_record = SubmissionHistory(
        submission_id = str(uuid.uuid4()), # Unique ID for this submission attempt
        report_id = generated_report.id, # Link to GeneratedReport
        submission_timestamp = datetime.utcnow(),
        status = "Pending", # Initial status
        report_filename = generated_report.report_filename, # Store filename in history too
        entry_count = generated_report.entry_count # Store entry count in history too
    )

    try:
        db.add(db_submission_record)
        # Update the status of the generated report record to indicate submission started
        generated_report.status = "SubmissionInProgress"
        generated_report.submission_id = db_submission_record.submission_id # Link submission to report
        db.add(generated_report) # Stage the update
        db.commit()
        db.refresh(db_submission_record) # Get the generated ID
        db.refresh(generated_report)
        logger.info(f"Simulated storing submission record {db_submission_record.submission_id} and updating report {generated_report.id} status to SubmissionInProgress.")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to store submission record or update report status in database: {e}", exc_info=True)
        send_alert("Critical", f"Database error storing submission record: {e}", {"module": "report-submission", "report_id": report_id, "error": str(e)})
        raise HTTPException(status_code=500, detail="Failed to record submission attempt")


    # --- TODO: Implement actual SDR submission logic ---
    # This is the critical external integration point.
    # It involves reading the report file from shared storage and sending it to the SDR.

    submission_successful = False
    sdr_response_data = None
    submission_error = None
    report_content = None

    try:
        # --- Simulate Reading Report File from Storage ---
        # In a real system, replace this with S3/Blob Storage SDK read operation
        # For simulation, read from the local path stored in the DB record
        report_storage_path = generated_report.report_storage_path # Get path from DB record
        if not os.path.exists(report_storage_path):
             raise FileNotFoundError(f"Simulated report file not found at {report_storage_path}")

        with open(report_storage_path, "rb") as f: # Read in binary mode
            report_content = f.read()
        logger.info(f"Simulated reading report file content from {report_storage_path}")


        # --- Simulate SDR Submission (using HTTP POST as example) ---
        # In a real scenario, replace this with actual SDR API call or SFTP logic.
        # Use the URL/credentials from environment variables.
        # SDR_SUBMISSION_URL = os.environ.get("SDR_SUBMISSION_URL") # Get from env vars
        # if not SDR_SUBMISSION_URL:
        #      raise ValueError("SDR_SUBMISSION_URL environment variable not set")

        # async with httpx.AsyncClient() as client:
        #     # Example HTTP POST submission
        #     response = await client.post(SDR_SUBMISSION_URL, content=report_content, timeout=300.0) # Allow long timeout
        #     response.raise_for_status() # Raise for bad status codes
        #     sdr_response_data = response.json() # Assuming SDR returns JSON response
        #     submission_successful = True # Assume success if no exception and status is good

        # --- Simple Simulation: Assume success for now ---
        logger.info(f"Simulating successful submission of {generated_report.report_filename} to SDR.")
        submission_successful = True
        sdr_response_data = {"status": "Accepted", "sdr_ack_id": f"ACK_{uuid.uuid4().hex[:8]}", "received_at": datetime.utcnow().isoformat()}
        # --- End Simulation ---


    except FileNotFoundError:
         submission_error = f"Report file not found during submission attempt: {report_storage_path}"
         logger.error(submission_error, exc_info=True)
         send_alert("Critical", submission_error, {"module": "report-submission", "report_id": report_id, "report_path": report_storage_path})
    except httpx.RequestError as exc:
        submission_error = f"HTTP Submission Failed: {exc}"
        logger.error(f"HTTP submission failed for {generated_report.report_filename}: {exc}", exc_info=True)
        send_alert("Error", f"SDR HTTP submission failed for {generated_report.report_filename}: {exc}", {"module": "report-submission", "report_id": report_id, "filename": generated_report.report_filename, "error": str(exc)})
    except Exception as e:
        submission_error = f"Unexpected Submission Error: {e}"
        logger.error(f"An unexpected error occurred during submission of {generated_report.report_filename}: {e}", exc_info=True)
        send_alert("Critical", f"Unexpected error during SDR submission: {e}", {"module": "report-submission", "report_id": report_id, "filename": generated_report.report_filename, "error": str(e)})


    # --- Update Submission Record and Generated Report Status ---
    try:
        # Retrieve the records again in case the session was closed or state is stale
        # Or pass the session to this part of the logic if it's separated
        db_submission_record = db.query(SubmissionHistory).filter(SubmissionHistory.id == db_submission_record.id).first()
        generated_report = db.query(GeneratedReport).filter(GeneratedReport.id == generated_report.id).first() # Re-fetch report record

        if db_submission_record and generated_report:
            if submission_successful:
                db_submission_record.status = "Submitted"
                db_submission_record.sdr_response_payload = sdr_response_data
                generated_report.status = "Submitted" # Update report status
                logger.info(f"Submission {db_submission_record.submission_id} for report {generated_report.id} marked as Submitted.")
                # TODO: Trigger next step: SDR acknowledgement processing (P3/later)
                # SDR might send an acknowledgement file/message later. A separate process would handle this.
            else:
                db_submission_record.status = "Failed"
                db_submission_record.error_details = submission_error
                generated_report.status = "SubmissionFailed" # Update report status
                logger.error(f"Submission {db_submission_record.submission_id} for report {generated_report.id} marked as Failed.")
                # TODO: Trigger error reporting to Error Monitoring module (already done via send_alert, but maybe a dedicated error record is needed)
                # TODO: Implement retry logic for failed submissions (e.g., queue for retry worker)

            db.add(db_submission_record)
            db.add(generated_report)
            db.commit()
            logger.info("Updated submission and report statuses in DB.")
        else:
             logger.error(f"Could not find submission or report record in DB to update status after submission attempt for report {report_id}.")
             send_alert("Critical", f"Failed to update DB status after submission attempt: {report_id}", {"module": "report-submission", "report_id": report_id})


    except Exception as e:
        db.rollback()
        logger.error(f"Critical database error updating status after submission: {e}", exc_info=True)
        send_alert("Critical", f"Database error updating status after submission: {e}", {"module": "report-submission", "report_id": report_id, "error": str(e)})
        # This is a critical failure in the submission module itself

    if submission_successful:
        return {"status": "success", "submission_id": db_submission_record.submission_id, "sdr_response": sdr_response_data}
    else:
        # If submission failed, raise an HTTPException
        raise HTTPException(status_code=500, detail=f"Report submission failed: {submission_error}")

# --- P3: Admin UI를 위한 API 엔드포인트 추가 ---
@app.get("/submissions")
async def get_submissions_for_ui(
    db: Session = Depends(get_db), # Use DB session
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Offset for pagination"),
    submission_id: Optional[str] = Query(None, description="Filter by submission ID (partial match)"),
    report_id: Optional[str] = Query(None, description="Filter by report ID"),
    status: Optional[str] = Query(None, description="Filter by submission status (e.g., Pending, Submitted, Failed)"),
    # TODO: Add filters for date range, entry count range
):
    """
    API endpoint for the Admin UI frontend to fetch submission history.
    Fetches from the database.
    """
    logger.info(f"Received request to list submissions with filters: submission_id={submission_id}, report_id={report_id}, status={status}, limit={limit}, offset={offset}")

    # Build SQLAlchemy query
    query = db.query(SubmissionHistory)

    if submission_id:
        query = query.filter(SubmissionHistory.submission_id.ilike(f"%{submission_id}%"))
    if report_id:
        query = query.filter(SubmissionHistory.report_id == report_id)
    if status:
        query = query.filter(SubmissionHistory.status == status)

    # Get total count before applying limit/offset
    total_count = query.count()

    # Apply ordering (e.g., by submission timestamp descending), limit, and offset
    submission_records = query.order_by(desc(SubmissionHistory.submission_timestamp)).offset(offset).limit(limit).all()

    # Convert SQLAlchemy objects to dictionaries for response
    submission_list = []
    for record in submission_records:
        record_dict = record.__dict__
        record_dict.pop('_sa_instance_state', None) # Remove SQLAlchemy internal state
        submission_list.append(record_dict)

    logger.info(f"Found {total_count} matching submission records. Returning {len(submission_list)} after pagination.")

    return {
        "status": "success",
        "total_count": total_count,
        "returned_count": len(submission_list),
        "offset": offset,
        "limit": limit,
        "submissions": submission_list
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for the Report Submission module.
    Checks database connectivity.
    """
    db_status = "ok"
    try:
        # Attempt to query the database to check connectivity
        db.query(SubmissionHistory).limit(1).all()
        db.query(GeneratedReport).limit(1).all() # Also check generated reports table
    except Exception as e:
        db_status = f"error: {e}"
        logger.error(f"Database health check failed: {e}", exc_info=True)
        send_alert("Critical", f"Database connectivity issue in Report Submission: {e}", {"module": "report-submission", "check": "db_connectivity"})

    # TODO: Add check for connectivity to File Storage (S3/Blob) if implemented
    # TODO: Add check for connectivity to SDR endpoint (if possible without submitting)

    return {"status": "ok", "database_status": db_status}

# To run this module locally:
# 1. Ensure your database is running.
# 2. Set the DATABASE_URL environment variable if not using SQLite.
# 3. Set ERROR_MONITOR_MODULE_URL env var if not using default.
# 4. Set SDR_SUBMISSION_URL or SFTP env vars for real submission (or keep simulation).
# 5. Ensure the REPORT_OUTPUT_DIR from Report Generation is accessible (if using local file sim).
# 6. Run uvicorn: uvicorn main:app --reload --port 8004
