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

