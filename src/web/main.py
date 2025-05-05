# src/web/main.py

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse # Example for serving a simple HTML page
from fastapi.staticfiles import StaticFiles # Example for serving static files
from typing import List, Dict, Any, Optional
import uvicorn
import httpx # Used for calling other internal services
import os

# src.common에서 로거 가져오기
from common.utils import logger

# TODO: Replace with actual Error Monitoring Service URL
# ERROR_MONITOR_SERVICE_URL = "http://error-monitoring-service:80/" # Example in K8s
ERROR_MONITOR_SERVICE_URL = "http://localhost:8005" # Local testing URL

# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

# --- Serve static files (e.g., HTML, CSS, JS for the Admin UI frontend) ---
# Assuming your frontend files are in a 'static' directory within src/web
# You would build your frontend (React/Vue/Angular) and place the output here.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"Serving static files from {STATIC_DIR}")
else:
    logger.warning(f"Static directory not found at {STATIC_DIR}. Static files will not be served.")


# --- Example HTML endpoint for the root (if serving a simple SPA) ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serves the main HTML file for the Admin UI.
    """
    html_file_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_file_path):
        with open(html_file_path, "r") as f:
            return f.read()
    else:
        return "<h1>Swap Reporting MVP Admin UI Backend</h1><p>Frontend index.html not found in ./static.</p>"


# --- API Endpoints for the Admin UI Frontend (Calling Error Monitoring Module) ---

@app.get("/api/errors")
async def get_errors_for_ui(
    status: Optional[str] = Query(None, description="Filter by error status"),
    source_module: Optional[str] = Query(None, description="Filter by source module"),
    trade_id: Optional[str] = Query(None, description="Filter by trade ID or UTI (partial match)"),
    limit: int = Query(100, description="Maximum number of errors to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    API endpoint for the Admin UI frontend to fetch error list.
    Calls the Error Monitoring module's /errors endpoint.
    """
    logger.info("Admin UI backend received request to fetch errors.")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module
            response = await client.get(
                f"{ERROR_MONITOR_SERVICE_URL}/errors",
                params={
                    "status": status,
                    "source_module": source_module,
                    "trade_id": trade_id,
                    "limit": limit,
                    "offset": offset
                },
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("Successfully fetched errors from Error Monitoring module.")
            return response.json() # Return the response from the Error Monitoring module

    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch errors from Error Monitoring module: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch errors: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching errors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching errors: {e}")


@app.get("/api/errors/{error_id}")
async def get_error_details_for_ui(error_id: str):
    """
    API endpoint for the Admin UI frontend to fetch details of a specific error.
    Calls the Error Monitoring module's /errors/{error_id} endpoint.
    """
    logger.info(f"Admin UI backend received request for error details: {error_id}")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module
            response = await client.get(
                f"{ERROR_MONITOR_SERVICE_URL}/errors/{error_id}",
                timeout=30.0
            )
            response.raise_for_status()
            logger.info(f"Successfully fetched error details for {error_id}.")
            return response.json() # Return the response from the Error Monitoring module

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Error not found")
        logger.error(f"HTTP error fetching error details for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=exc.response.status_code, detail=f"Failed to fetch error details: {exc.response.text}")
    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch error details for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch error details: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching error details for {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching error details: {e}")


@app.put("/api/errors/{error_id}/status")
async def update_error_status_for_ui(error_id: str, new_status: str):
    """
    API endpoint for the Admin UI frontend to update the status of an error.
    Calls the Error Monitoring module's /errors/{error_id}/status endpoint.
    """
    logger.info(f"Admin UI backend received request to update status for error {error_id} to {new_status}")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module
            response = await client.put(
                f"{ERROR_MONITOR_SERVICE_URL}/errors/{error_id}/status",
                params={"new_status": new_status},
                timeout=30.0
            )
            response.raise_for_status()
            logger.info(f"Successfully updated status for error {error_id}.")
            return response.json() # Return the response from the Error Monitoring module

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Error not found")
        logger.error(f"HTTP error updating status for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=exc.response.status_code, detail=f"Failed to update error status: {exc.response.text}")
    except httpx.RequestError as exc:
        logger.error(f"Failed to update status for error {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update error status: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while updating status for error {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error updating status: {e}")


@app.post("/api/errors/{error_id}/retry")
async def retry_error_processing_for_ui(error_id: str):
    """
    API endpoint for the Admin UI frontend to trigger retry processing for an error.
    Calls the Error Monitoring module's /errors/{error_id}/retry endpoint.
    """
    logger.info(f"Admin UI backend received request to retry processing for error {error_id}")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module
            response = await client.post(
                f"{ERROR_MONITOR_SERVICE_URL}/errors/{error_id}/retry",
                timeout=60.0 # Allow longer timeout for retry initiation
            )
            response.raise_for_status()
            logger.info(f"Successfully initiated retry for error {error_id}.")
            return response.json() # Return the response from the Error Monitoring module

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Error not found")
        logger.error(f"HTTP error initiating retry for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=exc.response.status_code, detail=f"Failed to initiate retry: {exc.response.text}")
    except httpx.RequestError as exc:
        logger.error(f"Failed to initiate retry for error {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initiate retry: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while initiating retry for error {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error initiating retry: {e}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Web module backend.
    """
    # Optionally, check the health of dependent services like Error Monitoring
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{ERROR_MONITOR_SERVICE_URL}/health", timeout=5.0)
            response.raise_for_status()
            error_monitor_status = response.json()
    except Exception as e:
        error_monitor_status = {"status": "down", "error": str(e)}
        logger.error(f"Error Monitoring health check failed: {e}")

    return {"status": "ok", "dependencies": {"error_monitoring": error_monitor_status}}

# To run this module locally:
# uvicorn main:app --reload --port 8006 # Assuming Admin UI backend runs on port 8006


#===================== integrating the database into the remaining modules and updating the inter-module communication to use environment variables, preparing for Kubernetes deployment.

# src/web/main.py

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse # Example for serving a simple HTML page
from fastapi.staticfiles import StaticFiles # Example for serving static files
from typing import List, Dict, Any, Optional
import uvicorn
import httpx # Used for calling other internal services
import os # To read environment variables

# src.common에서 로거 가져오기
from common.utils import logger

# TODO: Replace hardcoded URLs with Environment Variables injected by Kubernetes
# ERROR_MONITOR_SERVICE_URL = os.environ.get("ERROR_MONITOR_SERVICE_URL", "http://error-monitoring-service:80") # Example in K8s
# DATA_PROCESSING_SERVICE_URL = os.environ.get("DATA_PROCESSING_SERVICE_URL", "http://data-processing-service:80") # Example for querying processed data
# REPORT_GENERATION_SERVICE_URL = os.environ.get("REPORT_GENERATION_SERVICE_URL", "http://report-generation-service:80") # Example for querying reports
# REPORT_SUBMISSION_SERVICE_URL = os.environ.get("REPORT_SUBMISSION_SERVICE_URL", "http://report-submission-service:80") # Example for querying submissions

ERROR_MONITOR_SERVICE_URL = os.environ.get("ERROR_MONITOR_SERVICE_URL", "http://localhost:8005") # Default to Local testing URL
DATA_PROCESSING_SERVICE_URL = os.environ.get("DATA_PROCESSING_SERVICE_URL", "http://localhost:8001") # Default to Local testing URL
REPORT_GENERATION_SERVICE_URL = os.environ.get("REPORT_GENERATION_SERVICE_URL", "http://localhost:8003") # Default to Local testing URL
REPORT_SUBMISSION_SERVICE_URL = os.environ.get("REPORT_SUBMISSION_SERVICE_URL", "http://localhost:8004") # Default to Local testing URL


# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

# --- Serve static files (e.g., HTML, CSS, JS for the Admin UI frontend) ---
# Assuming your frontend files are in a 'static' directory within src/web
# You would build your frontend (React/Vue/Angular) and place the output here.
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"Serving static files from {STATIC_DIR}")
else:
    logger.warning(f"Static directory not found at {STATIC_DIR}. Static files will not be served.")
    # Create a dummy index.html for basic testing if static dir is missing
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "static")):
         os.makedirs(os.path.join(os.path.dirname(__file__), "static"), exist_ok=True)
         with open(os.path.join(os.path.dirname(__file__), "static", "index.html"), "w") as f:
              f.write("<h1>Admin UI Frontend Not Built</h1><p>Run your frontend build process and place files in ./static</p>")
         logger.info("Created dummy index.html")


# --- Example HTML endpoint for the root (if serving a simple SPA) ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Serves the main HTML file for the Admin UI.
    """
    html_file_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_file_path):
        with open(html_file_path, "r") as f:
            return f.read()
    else:
        # Fallback if static dir exists but index.html is missing
        return "<h1>Swap Reporting MVP Admin UI Backend</h1><p>Frontend index.html not found in ./static.</p>"


# --- API Endpoints for the Admin UI Frontend (Calling Other Modules) ---

# --- Error Management Endpoints ---
@app.get("/api/errors")
async def get_errors_for_ui(
    status: Optional[str] = Query(None, description="Filter by error status"),
    source_module: Optional[str] = Query(None, description="Filter by source module"),
    trade_id: Optional[str] = Query(None, description="Filter by trade ID or UTI (partial match)"),
    limit: int = Query(100, description="Maximum number of errors to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    API endpoint for the Admin UI frontend to fetch error list.
    Calls the Error Monitoring module's /errors endpoint.
    """
    logger.info("Admin UI backend received request to fetch errors.")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module using its URL from env var
            response = await client.get(
                f"{ERROR_MONITOR_SERVICE_URL}/errors",
                params={
                    "status": status,
                    "source_module": source_module,
                    "trade_id": trade_id,
                    "limit": limit,
                    "offset": offset
                },
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("Successfully fetched errors from Error Monitoring module.")
            return response.json() # Return the response from the Error Monitoring module

    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch errors from Error Monitoring module: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch errors: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching errors: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching errors: {e}")


@app.get("/api/errors/{error_id}")
async def get_error_details_for_ui(error_id: str):
    """
    API endpoint for the Admin UI frontend to fetch details of a specific error.
    Calls the Error Monitoring module's /errors/{error_id} endpoint.
    """
    logger.info(f"Admin UI backend received request for error details: {error_id}")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module using its URL from env var
            response = await client.get(
                f"{ERROR_MONITOR_SERVICE_URL}/errors/{error_id}",
                timeout=30.0
            )
            response.raise_for_status()
            logger.info(f"Successfully fetched error details for {error_id}.")
            return response.json() # Return the response from the Error Monitoring module

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Error not found")
        logger.error(f"HTTP error fetching error details for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=exc.response.status_code, detail=f"Failed to fetch error details: {exc.response.text}")
    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch error details for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch error details: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching error details for {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching error details: {e}")


@app.put("/api/errors/{error_id}/status")
async def update_error_status_for_ui(error_id: str, new_status: str, db: Session = Depends(get_db)): # Added DB dependency - might be needed for logging user action later
    """
    API endpoint for the Admin UI frontend to update the status of an error.
    Calls the Error Monitoring module's /errors/{error_id}/status endpoint.
    """
    logger.info(f"Admin UI backend received request to update status for error {error_id} to {new_status}")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module using its URL from env var
            response = await client.put(
                f"{ERROR_MONITOR_SERVICE_URL}/errors/{error_id}/status",
                params={"new_status": new_status},
                timeout=30.0
            )
            response.raise_for_status()
            logger.info(f"Successfully updated status for error {error_id}.")
            # TODO: Log the user action (who changed status, when) in the DB
            return response.json() # Return the response from the Error Monitoring module

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Error not found")
        logger.error(f"HTTP error updating status for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=exc.response.status_code, detail=f"Failed to update error status: {exc.response.text}")
    except httpx.RequestError as exc:
        logger.error(f"Failed to update status for error {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update error status: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while updating status for error {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error updating status: {e}")


@app.post("/api/errors/{error_id}/retry")
async def retry_error_processing_for_ui(error_id: str, db: Session = Depends(get_db)): # Added DB dependency for logging user action
    """
    API endpoint for the Admin UI frontend to trigger retry processing for an error.
    Calls the Error Monitoring module's /errors/{error_id}/retry endpoint.
    """
    logger.info(f"Admin UI backend received request to retry processing for error {error_id}")
    try:
        async with httpx.AsyncClient() as client:
            # Forward the request to the Error Monitoring module using its URL from env var
            response = await client.post(
                f"{ERROR_MONITOR_SERVICE_URL}/errors/{error_id}/retry",
                timeout=60.0 # Allow longer timeout for retry initiation
            )
            response.raise_for_status()
            logger.info(f"Successfully initiated retry for error {error_id}.")
            # TODO: Log the user action (who initiated retry, when) in the DB
            return response.json() # Return the response from the Error Monitoring module

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Error not found")
        logger.error(f"HTTP error initiating retry for {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=exc.response.status_code, detail=f"Failed to initiate retry: {exc.response.text}")
    except httpx.RequestError as exc:
        logger.error(f"Failed to initiate retry for error {error_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initiate retry: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while initiating retry for error {error_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error initiating retry: {e}")

# --- Add endpoints for querying other data (P3) ---

@app.get("/api/processed-data")
async def get_processed_data_for_ui(
    # Add query parameters for filtering, pagination, etc.
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Offset for pagination")
    # TODO: Add filters for UTI, date range, status, etc.
):
    """
    API endpoint for the Admin UI frontend to fetch processed data.
    Calls the Data Processing module's API (needs to be implemented there).
    """
    logger.info("Admin UI backend received request to fetch processed data.")
    try:
        async with httpx.AsyncClient() as client:
            # Call the Data Processing module's API (assuming it has a /processed-data endpoint)
            # You'll need to implement this endpoint in data-processing/main.py
            response = await client.get(
                f"{DATA_PROCESSING_SERVICE_URL}/processed-data",
                params={"limit": limit, "offset": offset},
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("Successfully fetched processed data from Data Processing module.")
            return response.json()

    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch processed data from Data Processing module: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch processed data: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching processed data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching processed data: {e}")

@app.get("/api/reports")
async def get_reports_for_ui(
    # Add query parameters for filtering, pagination, etc.
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Offset for pagination")
    # TODO: Add filters for filename, date range, status, etc.
):
    """
    API endpoint for the Admin UI frontend to fetch generated report info.
    Calls the Report Generation module's API (needs to be implemented there).
    """
    logger.info("Admin UI backend received request to fetch reports.")
    try:
        async with httpx.AsyncClient() as client:
            # Call the Report Generation module's API (assuming it has a /reports endpoint)
            # You'll need to implement this endpoint in report-generation/main.py
            response = await client.get(
                f"{REPORT_GENERATION_SERVICE_URL}/reports",
                params={"limit": limit, "offset": offset},
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("Successfully fetched reports from Report Generation module.")
            return response.json()

    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch reports from Report Generation module: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch reports: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching reports: {e}")

@app.get("/api/submissions")
async def get_submissions_for_ui(
    # Add query parameters for filtering, pagination, etc.
    limit: int = Query(100, description="Maximum number of records to return"),
    offset: int = Query(0, description="Offset for pagination")
    # TODO: Add filters for submission ID, report ID, date range, status, etc.
):
    """
    API endpoint for the Admin UI frontend to fetch submission history.
    Calls the Report Submission module's API (needs to be implemented there).
    """
    logger.info("Admin UI backend received request to fetch submissions.")
    try:
        async with httpx.AsyncClient() as client:
            # Call the Report Submission module's API (assuming it has a /submissions endpoint)
            # You'll need to implement this endpoint in report-submission/main.py
            response = await client.get(
                f"{REPORT_SUBMISSION_SERVICE_URL}/submissions",
                params={"limit": limit, "offset": offset},
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("Successfully fetched submissions from Report Submission module.")
            return response.json()

    except httpx.RequestError as exc:
        logger.error(f"Failed to fetch submissions from Report Submission module: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch submissions: {exc}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching submissions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Unexpected error fetching submissions: {e}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Web module backend.
    Checks connectivity to dependent services.
    """
    dependency_statuses = {}
    services_to_check = {
        "error_monitoring": ERROR_MONITOR_SERVICE_URL,
        "data_processing": DATA_PROCESSING_SERVICE_URL,
        "report_generation": REPORT_GENERATION_SERVICE_URL,
        "report_submission": REPORT_SUBMISSION_SERVICE_URL,
    }

    async with httpx.AsyncClient() as client:
        for service_name, url in services_to_check.items():
            health_url = f"{url}/health" # Assuming all modules have a /health endpoint
            try:
                response = await client.get(health_url, timeout=5.0)
                response.raise_for_status()
                dependency_statuses[service_name] = response.json()
            except Exception as e:
                dependency_statuses[service_name] = {"status": "down", "error": str(e)}
                logger.error(f"Health check failed for {service_name} ({health_url}): {e}")

    overall_status = "ok" if all(s.get("status") == "ok" for s in dependency_statuses.values()) else "degraded"

    return {"status": overall_status, "dependencies": dependency_statuses}

# To run this module locally:
# 1. Set environment variables for all dependent service URLs (ERROR_MONITOR_SERVICE_URL, etc.)
#    Example (Linux/macOS): export ERROR_MONITOR_SERVICE_URL="http://localhost:8005"
# 2. Ensure the 'static' directory exists and contains your frontend build (index.html, etc.).
# 3. Run uvicorn: uvicorn main:app --reload --port 8006
