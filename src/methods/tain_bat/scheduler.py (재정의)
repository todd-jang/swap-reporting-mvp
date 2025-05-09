# tain_bat/scheduler.py (재정의)

import datetime
import time
# 다른 모듈(예: AI 학습 서비스, 보고서 생성 서비스, 배치 처리 서비스) 임포트
# from ai_learning_service import trigger_weekly_model_update_workflow
# from reporting_service import trigger_daily_ktfc_report, trigger_cumulative_report
# from tain_bat.batch_processor import trigger_batch_anomaly_check_job # 배치 이상 탐지 실행 함수
# from common.utils import is_weekday, is_holiday, is_last_day_of_month # 날짜 유틸리티

class SwapReportingScheduler:
    def __init__(self):
        print("Scheduler 초기화...")
        # TODO: 스케줄링 엔진 초기화 (예: APScheduler, Celery Beat 등 실제 라이브러리 사용)

    def start(self):
        print("Scheduler 시작. 작업 대기 중...")
        # TODO: 스케줄링 엔진 시작

        # --- 정기 스케줄 등록 ---

        # 1. 주간 AI 모델 학습 및 업데이트 스케줄 (매주 주말)
        # 예: 매주 토요일 03:00에 실행
        # scheduler.add_job(trigger_weekly_model_update_workflow, 'cron', day_of_week='sat', hour=3, minute=0)
        print("  - 주간 AI 모델 업데이트 스케줄 등록 완료 (매주 토요일 03:00)")

        # 2. 일별 KTFC 보고서 생성 및 전송 스케줄 (주말/공휴일 제외 매일 05:00)
        # 예: 매주 월~금요일 05:00에 실행 (공휴일 제외 로직은 함수 내 또는 스케줄러 설정에서 처리)
        # scheduler.add_job(trigger_daily_ktfc_report_if_weekday, 'cron', day_of_week='mon-fri', hour=5, minute=0)
        print("  - 일별 KTFC 보고서 스케줄 등록 완료 (주중 매일 05:00)")

        # 3. 배치 이상 탐지 실행 스케줄 (예: 매일 특정 시간 또는 데이터 유입 완료 후)
        # 예: 매일 04:00에 전날 데이터 전체에 대한 배치 이상 탐지 실행
        # scheduler.add_job(trigger_batch_anomaly_check_job, 'cron', hour=4, minute=0)
        print("  - 일별 배치 이상 탐지 스케줄 등록 완료 (매일 04:00)")


        # 4. 누적 이상 데이터 보고서 스케줄 (분기별, 반기별, 연간)
        # 예: 매월 1일 특정 시간에 실행하고 함수 내에서 분기/반기/연간 조건 판단
        # scheduler.add_job(trigger_cumulative_report_if_due, 'cron', day='1', hour=6)
        print("  - 누적 보고서 스케줄 등록 완료 (매월 1일 06:00)")


        # TODO: 스케줄링 엔진이 계속 실행되도록 유지
        try:
            while True:
                time.sleep(60) # 1분마다 확인 등 (실제 엔진은 내부적으로 관리)
        except (KeyboardInterrupt, SystemExit):
            self.shutdown()

    def shutdown(self):
        print("Scheduler 종료 중...")
        # TODO: 스케줄링 엔진 종료

    # --- 스케줄에 의해 호출될 개념적 함수 (다른 서비스/모듈의 함수를 호출) ---

    def trigger_weekly_model_update_workflow(self):
        """주간 AI 모델 학습 워크플로우 시작 함수."""
        print(">>> 스케줄: 주간 AI 모델 업데이트 트리거 <<<")
        # TODO: 별도의 AI 학습 서비스에 워크플로우 시작 요청 또는 관련 배치 스크립트 실행
        # ai_learning_service.trigger_full_update()

    def trigger_daily_ktfc_report_if_weekday(self):
        """주중일 경우 일별 KTFC 보고서 생성 및 전송 함수."""
        today = datetime.date.today()
        # if is_weekday(today) and not is_holiday(today):
        print(f">>> 스케줄: 일별 KTFC 보고서 트리거 ({today}) <<<")
        reporting_date = today - datetime.timedelta(days=1) # 전일 데이터
        # TODO: 보고서 생성 및 전송 서비스/모듈 호출
        # reporting_service.trigger_daily_report_workflow(reporting_date)
        # else:
        # print(f">>> 스케줄: 주말/공휴일 ({today}). 일별 보고 건너뛰기 <<<")


    def trigger_batch_anomaly_check_job(self):
        """배치 데이터 이상 탐지 작업 트리거 함수."""
        print(">>> 스케줄: 배치 이상 탐지 작업 트리거 <<<")
        # TODO: TainBat의 배치 이상 탐지 처리 함수 또는 Job 실행 요청
        # tain_bat.batch_processor.trigger_batch_anomaly_check()


    def trigger_cumulative_report_if_due(self):
        """분기/반기/연간 조건 충족 시 누적 보고서 생성 함수."""
        today = datetime.date.today()
        # if not is_weekday(today) or is_holiday(today): # 주말이나 공휴일에는 실행 안 함 가정
        #      return

        # if is_last_day_of_month(today):
        #      if today.month in [3, 6, 9, 12]:
        #          print(f">>> 스케줄: 분기별 누적 보고서 트리거 ({today}) <<<")
        #          # reporting_service.trigger_cumulative_report('quarterly', today)
        #      if today.month in [6, 12]:
        #          print(f">>> 스케줄: 반기별 누적 보고서 트리거 ({today}) <<<")
        #          # reporting_service.trigger_cumulative_report('semiannual', today) # 분기 후 실행 등 로직 필요
        #      if today.month == 12:
        #          print(f">>> 스케줄: 연간 누적 보고서 트리거 ({today}) <<<")
        #          # reporting_service.trigger_cumulative_report('annual', today) # 반기 후 실행 등 로직 필요
        print(">>> 스케줄: 누적 보고서 트리거 (조건 판단은 함수 내에서) <<<")

# 예시: 스케줄러 시작
if __name__ == "__main__":
     # scheduler = SwapReportingScheduler()
     # scheduler.start()
     print("scheduler.py 파일은 스케줄링 정의만 포함합니다.")
     print("실제 실행 시 스케줄링 엔진에 의해 등록된 함수들이 호출됩니다.")
