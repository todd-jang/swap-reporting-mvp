# src/data-ingestion/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uvicorn
# import httpx # 실제 HTTP 호출 시 사용

# src.common에서 로거 및 임시 저장소 가져오기
from common.utils import logger, ingested_data_store

# TODO: Replace direct function calls with actual API calls or message queue publishing
# For demonstration, we simulate calls by directly importing and calling functions
# from other modules. This is NOT how a distributed system should work.
# In a real K8s environment, modules communicate via Services (HTTP/gRPC) or MQ.
from data_processing.main import process_swap_data as call_processing_module

# --- 수신할 데이터 모델 정의 (CFTC Part 45/43 데이터 요소 참고 예시) ---
class SwapData(BaseModel):
    """
    Example model for raw swap trade data received from external systems.
    This should reflect the format of data received from your specific sources.
    """
    trade_id: str = Field(..., description="Internal trade identifier from source system")
    action: str = Field(..., description="Action type (e.g., NEWT, AMND, TERM)")
    instrument_type: str = Field(..., description="Type of swap instrument (e.g., IRS, CDS)")
    asset_class: str = Field(..., description="Asset class (e.g., IR, CR, FX, EQ, CO)")
    effective_date: str = Field(..., description="Swap effective date (YYYY-MM-DD)")
    termination_date: str = Field(..., description="Swap termination date (YYYY-MM-DD)")
    notional_amount: float = Field(..., description="Notional amount of the swap")
    notional_currency: str = Field(..., description="Currency of the notional amount")
    party_a_lei: str = Field(..., description="LEI of party A")
    party_b_lei: str = Field(..., description="LEI of party B")
    price: float | None = Field(None, description="Price or rate")
    price_currency: str | None = Field(None, description="Currency of the price")
    # ... Add other relevant raw data fields

# --- FastAPI 앱 인스턴스 생성 ---
app = FastAPI()

@app.post("/ingest")
async def ingest_swap_data(data: List[SwapData]):
    """
    API endpoint to receive swap trade data from external sources.
    Stores data temporarily and forwards it to the processing module.
    """
    logger.info(f"Received {len(data)} swap data entries for ingestion.")

    # Store received data in the in-memory store
    ingested_data_dicts = [entry.model_dump() for entry in data]
    ingested_data_store.extend(ingested_data_dicts)
    logger.info(f"Stored {len(data)} entries in ingestion store. Total: {len(ingested_data_store)}")

    # Forward data to the processing module
    # In a real system, this would be an async HTTP call or sending to a message queue
    try:
        # Simulate calling the processing module function directly
        # Replace with: await client.post(PROCESSING_MODULE_URL, json=ingested_data_dicts)
        processing_response = await call_processing_module(ingested_data_dicts)
        logger.info(f"Processing module responded: {processing_response}")
        # TODO: Handle processing module response (e.g., check status, log errors)

    except Exception as e:
        logger.error(f"Failed to forward data to processing module: {e}", exc_info=True)
        # TODO: Implement retry logic or move data to a Dead Letter Queue (DLQ)

    return {"status": "success", "received_count": len(data), "processing_status": "forwarded"} # Indicate forwarding initiated

@app.get("/health")
async def health_check():
    """
    Health check endpoint for the Data Ingestion module.
    """
    return {"status": "ok", "ingested_count_in_store": len(ingested_data_store)}

# To run this module locally:
# uvicorn main:app --reload --port 8000

#=====================with real database

# src/common/utils.py

import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

# --- SQLAlchemy Imports ---
from sqlalchemy import create_engine, Column, String, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB # Use JSONB for PostgreSQL if needed

# --- Database Configuration (using Environment Variables) ---
# In a real K8s deployment, these would be injected via Secrets or ConfigMaps
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./swap_reporting_mvp.db") # Default to SQLite for local dev

# --- Database Engine and Session Setup ---
# create_engine: Creates a database engine instance
# pool_pre_ping=True: Helps handle dropped connections
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# declarative_base(): The base class for declarative models
Base = declarative_base()

# sessionmaker: Configures a Session class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session (for FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SQLAlchemy Models (Database Schema Definition) ---

# Raw Ingested Data Table
class RawIngestedData(Base):
    __tablename__ = "raw_ingested_data"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4())) # Unique ID for each record
    trade_id = Column(String, index=True) # Original ID from source
    action = Column(String)
    instrument_type = Column(String)
    asset_class = Column(String)
    effective_date = Column(String) # Store as string initially, validate format later
    termination_date = Column(String) # Store as string initially
    notional_amount = Column(Float)
    notional_currency = Column(String)
    party_a_lei = Column(String)
    party_b_lei = Column(String)
    price = Column(Float, nullable=True)
    price_currency = Column(String, nullable=True)
    raw_payload = Column(JSON) # Store the original JSON payload
    ingestion_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Ingested") # e.g., Ingested, Processed, Failed

# Processed Data Table (Standardized)
class ProcessedSwapDataDB(Base): # Renamed to avoid conflict with Pydantic model
    __tablename__ = "processed_swap_data"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    unique_transaction_identifier = Column(String, unique=True, index=True) # UTI
    reporting_counterparty_lei = Column(String)
    other_counterparty_lei = Column(String)
    action_type = Column(String)
    event_type = Column(String, nullable=True)
    asset_class = Column(String)
    effective_date = Column(String)
    termination_date = Column(String)
    notional_amount = Column(Float, nullable=True)
    notional_currency = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    price_currency = Column(String, nullable=True)
    # ... Add other CDE fields as columns ...
    processing_status = Column(String, default="Processed") # e.g., Processed, ProcessedWithErrors
    processing_errors = Column(JSON) # Store processing errors as JSON (or JSONB)
    original_raw_data_id = Column(String) # Link back to raw data (Optional but good practice)
    processing_timestamp = Column(DateTime, default=datetime.utcnow)
    validation_status = Column(String, default="Pending") # Pending, Valid, Invalid

# Validation Results Table (Can be combined with Processed data or separate)
# Let's keep it separate for clarity of validation results history
class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    unique_transaction_identifier = Column(String, index=True) # Link to Processed data via UTI
    is_valid = Column(Boolean)
    errors = Column(JSON) # Store validation errors as JSON (or JSONB)
    validation_timestamp = Column(DateTime, default=datetime.utcnow)
    processed_data_id = Column(String, nullable=True) # Link to Processed data via its ID

# Errors Table (P3 Error Management)
class ErrorRecord(Base):
    __tablename__ = "error_records"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    trade_id = Column(String, index=True, nullable=True) # Original ID or UTI
    source_module = Column(String) # e.g., data-processing, validation, report-submission
    error_messages = Column(JSON) # Store error messages as JSON (or JSONB)
    data_payload = Column(JSON) # Store the data associated with the error (raw or processed)
    original_source_data_payload = Column(JSON, nullable=True) # Store original raw data if available
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Open") # e.g., Open, Investigating, Resolved, Closed
    assigned_to = Column(String, nullable=True)
    severity = Column(String, default="Error") # e.g., Info, Warning, Error, Critical

# Generated Reports Table (P2 Report Generation)
class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    report_filename = Column(String, unique=True, index=True) # Name of the generated file
    report_storage_path = Column(String) # Path or identifier in shared storage
    entry_count = Column(Integer) # Number of entries in the report
    generation_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Generated") # e.g., Generated, Submitted, SubmissionFailed, Acknowledged
    submission_id = Column(String, nullable=True) # Link to SubmissionHistory

# Submission History Table (P2 Report Submission)
class SubmissionHistory(Base):
    __tablename__ = "submission_history"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String, unique=True, index=True) # Unique ID for this submission attempt
    report_id = Column(String) # Link to GeneratedReport
    submission_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Pending") # e.g., Pending, Submitted, SubmissionFailed, SDR_Accepted, SDR_Rejected
    sdr_response_payload = Column(JSON, nullable=True) # Store SDR response details
    error_details = Column(Text, nullable=True) # Store submission error details

# --- Create Database Tables ---
# This should be run once to initialize the database schema.
# In production, use Alembic for migrations.
def create_database_tables():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created (if they didn't exist).")

# --- Logger Setup ---
def setup_logger(name, level=logging.INFO):
    """
    Sets up a basic logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Project's main logger
logger = setup_logger("swap-reporting-mvp")

# --- 예시 식별자 생성 함수 ---
def generate_uti(trade_data: dict) -> str:
    """
    Example function to generate a Unique Transaction Identifier (UTI).
    """
    timestamp = int(time.time() * 1000)
    unique_part = str(uuid.uuid4()).split('-')[0]
    source_id = trade_data.get('trade_id', 'UNKNOWN')
    return f"MVP-{source_id}-{timestamp}-{unique_part}".replace('_', '-')

def validate_lei(lei: str) -> bool:
    """
    Example function to validate a Legal Entity Identifier (LEI).
    """
    if not lei or not isinstance(lei, str):
        return False
    if len(lei) != 20 or not lei.isalnum():
        return False
    # TODO: Add actual LEI validation logic (checksum, GLEIF database lookup)
    return True

# --- 예시 알림 함수 ---
def send_alert(severity: str, message: str, details: Optional[Dict[str, Any]] = None):
    """
    Simulates sending an alert based on severity.
    """
    alert_timestamp = datetime.now().isoformat()
    alert_info = {
        "timestamp": alert_timestamp,
        "severity": severity.upper(),
        "message": message,
        "details": details if details is not None else {}
    }
    if severity.lower() == 'critical' or severity.lower() == 'error':
        logger.error(f"ALERT! {severity.upper()}: {message}", extra=alert_info)
        # TODO: Integrate with Alertmanager API or other alerting system
    elif severity.lower() == 'warning':
        logger.warning(f"ALERT! {severity.upper()}: {message}", extra=alert_info)
        # TODO: Integrate with alerting system
    else:
        logger.info(f"ALERT! {severity.upper()}: {message}", extra=alert_info)

# --- Run table creation on startup (for local dev) ---
# In production, use Alembic migrations instead of calling this directly
# create_database_tables() # Uncomment to create tables when utils is imported
