#!/bin/bash

# scripts/run_sample_workflow.sh

# 이 스크립트는 각 서비스의 컨테이너가 이미 빌드되어 있다고 가정합니다.
# Docker Hub 또는 로컬 이미지 저장소에 이미지가 있다고 가정합니다.

# --- 서비스 실행 예시 (Docker Compose 사용 시) ---
# 대부분의 개발/테스트 환경 및 소규모 배포에서 Docker Compose를 사용합니다.
# docker-compose.yaml 파일에 모든 서비스 정의가 있어야 합니다.
# echo "--- Docker Compose로 전체 서비스 실행 시도 ---"
# docker-compose up -d # 백그라운드로 서비스 실행
# if [ $? -eq 0 ]; then
#     echo "Docker Compose 서비스 실행 성공."
# else
#     echo "Docker Compose 서비스 실행 실패."
#     exit 1
# fi

# --- 특정 워크플로우 순차 실행 예시 ---
# (서비스가 개별적으로 또는 컨테이너로 실행 중이라고 가정)

echo "--- TainTube 파일 처리 워크플로우 시뮬레이션 시작 ---"
WATCH_DIR="./watch"
PROCESSED_DIR="./processed"
mkdir -p $WATCH_DIR $PROCESSED_DIR # 디렉터리 생성

# 감시 디렉터리에 가상 파일 생성 (TainTube/file_listener가 감지할 수 있도록)
echo "UTI,Data..." > $WATCH_DIR/sample_swap_data_001.csv
echo "UTI,Data..." > $WATCH_DIR/sample_swap_data_002.csv

# TainTube 파일 처리 리스너 실행 (이것은 장시간 실행될 서비스)
# 실제로는 컨테이너로 백그라운드 실행됩니다.
# python tain_tube/file_listener.py --watch-dir $WATCH_DIR --processed-dir $PROCESSED_DIR & # 백그라운드 실행 예시
echo "TainTube file_listener 실행 시뮬레이션 (실제로는 컨테이너로 실행됨)..."
# file_listener 실행 시뮬레이션 함수 호출
python -c "from tain_tube.file_listener import listen_for_files; listen_for_files('$WATCH_DIR', '$PROCESSED_DIR', interval_seconds=1)" & # 예시 실행 (짧은 감시 주기)
TAINTUBE_PID=$! # 백그라운드 프로세스 ID 저장
echo "TainTube file_listener 시뮬레이션 PID: $TAINTUBE_PID"

# 잠시 대기하여 TainTube가 파일을 감지하고 처리하도록 함
echo "파일 처리 대기 중 (15초)..."
sleep 15

echo "--- TainBat 배치 처리 실행 시뮬레이션 시작 ---"
# TainBat 배치 처리 실행 (예: 전날 데이터 처리)
# 실제로는 Scheduler에 의해 정해진 시간에 실행됩니다.
# python tain_bat/batch_processor.py --date yesterday # 예시 배치 처리 스크립트 호출
echo "TainBat batch_processor 실행 시뮬레이션 (Scheduler에 의해 트리거됨)..."
# batch_processor 실행 시뮬레이션 함수 호출 (전날 데이터 처리)
python -c "import datetime; from tain_bat.batch_processor import run_daily_batch_processing; run_daily_batch_processing(datetime.date.today() - datetime.timedelta(days=1))"
BATCH_EXIT_STATUS=$?

if [ $BATCH_EXIT_STATUS -eq 0 ]; then
    echo "TainBat 배치 처리 시뮬레이션 성공."
else
    echo "TainBat 배치 처리 시뮬레이션 실패."
    # TODO: 오류 알림 등 후처리
fi


echo "--- 실시간 데이터 처리 서비스 실행 시뮬레이션 (TainOn) ---"
# TainOn 실시간 데이터 처리 서비스 실행 (이것도 장시간 실행될 서비스)
# 실제로는 컨테이너로 백그라운드 실행됩니다.
# python tain_on/realtime_service.py & # 예시 실행
echo "TainOn realtime_listener 실행 시뮬레이션 (실제로는 컨테이너로 실행됨)..."
# realtime_listener 실행 시뮬레이션 함수 호출
python -c "from tain_on.realtime_listener import RealtimeDataListener; listener = RealtimeDataListener({}); listener.start()" &
TAINON_PID=$!
echo "TainOn realtime_listener 시뮬레이션 PID: $TAINON_PID"

# AI 추론 서비스 실행 (TainOn/TainBat가 호출할 서비스)
# 실제로는 컨테이너로 백그라운드 실행됩니다.
# uvicorn ai_inference_service.inference_api:app --host 0.0.0.0 --port 8001 &
echo "AI Inference Service API 실행 시뮬레이션 (실제로는 컨테이너로 실행됨)..."
# API 서버 실행은 별도의 스크립트나 Dockerfile CMD에서 수행. 여기서는 개념만.
echo "API 서버는 http://localhost:8001 에서 실행될 것으로 가정합니다."


# 잠시 대기하여 서비스들이 실행될 시간을 줌
echo "서비스 실행 대기 중 (5초)..."
sleep 5

# UI 백엔드 실행 (사용자 요청 처리 API)
# 실제로는 컨테이너로 백그라운드 실행됩니다.
# uvicorn ui_backend.api:app --host 0.0.0.0 --port 8000 &
echo "UI Backend Service API 실행 시뮬레이션 (실제로는 컨테이너로 실행됨)..."
# API 서버 실행은 별도의 스크립트나 Dockerfile CMD에서 수행. 여기서는 개념만.
echo "UI Backend API 서버는 http://localhost:8000 에서 실행될 것으로 가정합니다."


echo "--- 샘플 워크플로우 스크립트 실행 완료 ---"
echo "실행된 백그라운드 프로세스들을 수동으로 종료해야 할 수 있습니다 (ps aux | grep python, kill <PID>)."

# 실행 예시 함수 호출 시 사용한 백그라운드 프로세스 종료 (옵션)
# kill $TAINTUBE_PID
# kill $TAINON_PID
