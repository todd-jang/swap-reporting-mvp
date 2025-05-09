재정의된 파일들의 연동:

realtime_listener.py는 외부로부터 실시간 데이터를 수신합니다.
수신된 데이터 레코드를 tainon_processor.py의 process_realtime_swap_data 함수로 전달합니다.
tainon_processor.py는 전달받은 데이터를 전처리하고, 미리 로딩해 둔 AI 모델(deployed_ensemble_model)을 사용하여 이상치 추론을 수행합니다.
이상치 추론 결과와 현재 시간 조건을 확인하여, 필요시 reporting_service(개념적인 별도 서비스)의 함수(trigger_immediate_anomaly_alert, generate_immediate_anomaly_report)를 호출하여 Alert 및 보고서 생성을 트리거하거나, 정상 데이터 처리 함수를 호출합니다.
scheduler.py는 정해진 스케줄에 따라 tainon_processor.py를 직접 호출하지는 않지만, 별도의 AI 학습 서비스나 TainBat의 배치 이상 탐지 함수(trigger_batch_anomaly_check_job), 보고서 생성 서비스 함수(trigger_daily_ktfc_report_if_weekday 등)를 호출하여 전체 워크플로우를 조율합니다.
이러한 방식으로 각 파일은 자신의 명확한 역할(스케줄링, 수신, 실시간 처리)을 수행하며, 함수 호출을 통해 다른 컴포넌트와 상호 작용하여 복잡한 스왑 데이터 보고 워크플로우를 실현합니다.
