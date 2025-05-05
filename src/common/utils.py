# src/common/utils.py

import logging
import time
import uuid
from typing import List, Dict, Any

# 로거 설정 유틸리티
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

# 프로젝트의 기본 로거 설정
logger = setup_logger("swap-reporting-mvp")

# --- 임시 인메모리 저장소 (실제 운영 시 DB, MQ 등으로 대체 필요) ---
# In-memory storage for demonstration purposes.
# In a real system, replace with persistent storage (Database)
# and message queues for inter-module communication.

# 수집된 원시 데이터 임시 저장
ingested_data_store: List[Dict[str, Any]] = []
# 처리/정규화된 데이터 임시 저장
processed_data_store: List[Dict[str, Any]] = []
# 유효성 검사 결과 임시 저장 (유효/무효 데이터 및 오류 정보)
validation_results_store: List[Dict[str, Any]] = []
# 유효하지 않은 데이터 임시 저장 (오류 관리를 위해)
invalid_data_store: List[Dict[str, Any]] = []

# --- 예시 식별자 생성 함수 (실제 규제/표준에 맞춰 구현 필요) ---
def generate_uti(trade_data: dict) -> str:
    """
    Example function to generate a Unique Transaction Identifier (UTI).
    In a real implementation, this should follow regulatory standards (e.g., ISO 23897)
    and likely incorporate internal identifiers, timestamps, etc.
    """
    # Example: Combine timestamp, a short UUID part, and a prefix
    timestamp = int(time.time() * 1000)
    unique_part = str(uuid.uuid4()).split('-')[0]
    source_id = trade_data.get('trade_id', 'UNKNOWN')
    # A more robust UTI might include reporting counterparty LEI or internal system ID
    return f"MVP-{source_id}-{timestamp}-{unique_part}".replace('_', '-') # Ensure valid characters

def validate_lei(lei: str) -> bool:
    """
    Example function to validate a Legal Entity Identifier (LEI).
    In a real implementation, this should involve checking the format (20 alphanumeric characters)
    and potentially verifying against a GLEIF database or a cached list of valid LEIs.
    """
    if not lei or not isinstance(lei, str):
        return False
    # Basic format check: 20 alphanumeric characters (simplified)
    if len(lei) != 20 or not lei.isalnum():
        return False
    # TODO: Add actual LEI validation logic (e.g., checksum, GLEIF database lookup)
    return True # Assume valid if basic format matches for this example

# ============== update the P1 modules to use the simulated database and call the next modules in the pipeline.

# src/common/utils.py

import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

# 로거 설정 유틸리티
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

# 프로젝트의 기본 로거 설정
logger = setup_logger("swap-reporting-mvp")

# --- 임시 인메모리 저장소 (실제 운영 시 DB, MQ 등으로 대체 필요) ---
# In-memory storage for demonstration purposes.
# In a real system, replace with persistent storage (Database like PostgreSQL, MongoDB)
# and message queues (like Kafka, RabbitMQ) for inter-module communication.

# Simulate a database table for raw ingested data
raw_ingested_db: List[Dict[str, Any]] = []
# Simulate a database table for processed/normalized data
processed_data_db: List[Dict[str, Any]] = []
# Simulate a database table for validation results
validation_results_db: List[Dict[str, Any]] = []
# Simulate a database table for errors (P3 Error Management)
errors_db: List[Dict[str, Any]] = []
# Simulate a database table for generated reports (P2 Report Generation)
generated_reports_db: List[Dict[str, Any]] = []
# Simulate a database table for submission history (P2 Report Submission)
submission_history_db: List[Dict[str, Any]] = []


# --- 예시 식별자 생성 함수 (실제 규제/표준에 맞춰 구현 필요) ---
def generate_uti(trade_data: dict) -> str:
    """
    Example function to generate a Unique Transaction Identifier (UTI).
    In a real implementation, this should follow regulatory standards (e.g., ISO 23897)
    and likely incorporate internal identifiers, timestamps, etc.
    """
    # Example: Combine timestamp, a short UUID part, and a prefix
    timestamp = int(time.time() * 1000)
    unique_part = str(uuid.uuid4()).split('-')[0]
    source_id = trade_data.get('trade_id', 'UNKNOWN')
    # A more robust UTI might include reporting counterparty LEI or internal system ID
    return f"MVP-{source_id}-{timestamp}-{unique_part}".replace('_', '-') # Ensure valid characters

def validate_lei(lei: str) -> bool:
    """
    Example function to validate a Legal Entity Identifier (LEI).
    In a real implementation, this should involve checking the format (20 alphanumeric characters)
    and potentially verifying against a GLEIF database or a cached list of valid LEIs.
    """
    if not lei or not isinstance(lei, str):
        return False
    # Basic format check: 20 alphanumeric characters (simplified)
    if len(lei) != 20 or not lei.isalnum(): # isalnum checks for alphanumeric
        return False
    # TODO: Add actual LEI validation logic (e.g., checksum, GLEIF database lookup via external API)
    # For this example, we'll consider 20 alphanumeric chars as valid format.
    return True

# --- 예시 알림 함수 (P3 Error Management) ---
def send_alert(severity: str, message: str, details: Optional[Dict[str, Any]] = None):
    """
    Simulates sending an alert based on severity.
    In a real system, this would integrate with Alertmanager, email, Slack, PagerDuty, etc.
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

    # For demonstration, just log the alert
    # In a real system, this would trigger an external alert notification

#=================== more over the simulated ...
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

