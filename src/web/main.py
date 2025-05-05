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
