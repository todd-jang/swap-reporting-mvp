# --- AI 학습 및 업데이트 워크플로우 (TainBat Scheduler 또는 별도 서비스) ---

def schedule_weekly_model_update():
    """
    매주 주말에 실행되도록 스케줄링된 함수.
    """
    if is_weekend(datetime.date.today()): # is_weekend, is_holiday 함수 필요
        print(">>> 주간 모델 업데이트 스케줄 시작 <<<")
        last_week_start, last_week_end = get_last_week_date_range() # 날짜 계산 함수

        # 1. 데이터 샘플링 및 로딩
        training_data_features = sample_and_load_data(data_config, last_week_start, last_week_end, sample_rate="hourly") # 시간당 샘플링

        if training_data_features is None or training_data_features.shape[0] == 0:
            print("  - 지난 주 샘플링 데이터 없음. 모델 업데이트 건너뜜.")
            return

        # 2. 여러 이상치 탐지 모델 학습
        model_configs = [
            {'name': 'IsolationForest', 'params': {'contamination': 0.05}},
            {'name': 'OneClassSVM', 'params': {'nu': 0.05}},
            {'name': 'Autoencoder', 'params': {'encoding_dim': 2}}, # 실제 파라미터 필요
        ]
        trained_individual_models = train_multiple_anomaly_models(training_data_features, model_configs)

        if not trained_individual_models:
             print("  - 학습 완료된 개별 모델 없음. 앙상블 구성 및 배포 건너뛰기.")
             return

        # 3. 모델 성능 평가 및 비교 (평가 데이터셋 필요)
        evaluation_features, evaluation_labels = load_evaluation_dataset() # 별도 라벨링된 평가 데이터셋 로딩 함수
        comparison_results = evaluate_and_compare_models(trained_individual_models, evaluation_features, evaluation_labels)

        # 4. 앙상블 모델 구성 (앙상블 트리)
        # 여러 모델의 예측 결과(점수 또는 라벨)를 입력으로 받아 최종 이상치 여부를 판단하는 또 다른 모델 (예: 결정 트리, 로지스틱 회귀)
        ensemble_model = build_ensemble_tree(trained_individual_models, evaluation_features, evaluation_labels) # 앙상블 학습 함수 (개별 모델 결과 기반 학습)

        # 5. 앙상블 모델 저장 및 배포
        current_model_version = time.strftime("%Y%m%d%H%M%S")
        deployed_ensemble_model_path = save_and_deploy_model(ensemble_model, 'EnsembleAnomalyDetector', version=current_model_version)

        # 6. 모델 재확인용 최저 성능 모델 식별 및 저장 (요청 사항 반영)
        if comparison_results:
             lowest_model_name = identify_lowest_performing_model(comparison_results)
             if lowest_model_name in trained_individual_models:
                 # 최저 성능 모델도 별도로 저장/배포하여 '재확인' 로직에서 로딩 가능하도록
                 save_and_deploy_model(trained_individual_models[lowest_model_name], f'{lowest_model_name}_LowestPerf', version=current_model_version)


        # TODO: 배포된 모델 정보 (경로, 버전)를 TainOn, TainBat 등이 사용하도록 업데이트 (DB, 설정 파일 등)

        print(">>> 주간 모델 업데이트 스케줄 완료 <<<")


# --- 실시간 데이터 처리 및 이상 탐지 (TainOn 역할) ---

# TainOn 서비스 초기 로딩 시 또는 모델 업데이트 감지 시
deployed_ensemble_model = None # 배포된 앙상블 모델 객체
# deployed_lowest_model = None # 재확인용 최저 성능 모델 (필요시 로딩)

def load_current_deployed_models():
    """배포된 최신 모델을 로딩하는 함수 (TainOn 시작 시 또는 업데이트 감지 시 호출)."""
    global deployed_ensemble_model # 전역 변수 사용 예시
    # global deployed_lowest_model # 전역 변수 사용 예시

    print("\n--- TainOn: 배포된 모델 로딩 ---")
    # TODO: 모델 저장소에서 최신 앙상블 모델 경로/버전 조회
    latest_ensemble_version = get_latest_model_version('EnsembleAnomalyDetector')
    if latest_ensemble_version:
        deployed_ensemble_model = load_deployed_model('EnsembleAnomalyDetector', version=latest_ensemble_version)
        # TODO: 필요시 최저 성능 모델도 로딩 (get_latest_model_version('IsolationForest_LowestPerf') 등)


def process_realtime_swap_data(data_record):
    """
    TainTube로부터 실시간 스왑 데이터 레코드가 들어올 때 호출되는 함수.
    """
    print(f"\n>>> TainOn: 실시간 데이터 처리 시작 (레코드: {data_record.get('UNIQUE_ID')}) <<<")
    if deployed_ensemble_model is None:
        print("  - 모델 로딩 안됨. 이상 탐지 건너뛰고 정상 처리.")
        # TODO: 모델 로딩 실패 알림 및 정상 처리 로직
        process_normal_realtime_record(data_record)
        return

    # 1. 데이터 전처리 (실시간 데이터에 맞게)
    features = preprocess_realtime_record(data_record) # 특징 추출 및 전처리 함수

    # 2. 앙상블 모델로 이상치 평가
    ensemble_score = deployed_ensemble_model.decision_function(features.reshape(1, -1))[0] # Shape 맞추기
    ensemble_prediction = deployed_ensemble_model.predict(features.reshape(1, -1))[0] # -1 또는 1

    is_anomaly = (ensemble_prediction == -1) # 앙상블 모델 예측 결과로 이상치 판단

    # 3. 이상 탐지 결과 기반 처리
    if is_anomaly:
        print(f"  - 이상 탐지됨 by 앙상블 모델. 점수: {ensemble_score:.4f}")
        # TODO: 재확인 로직 필요 시 (예: 최저 성능 모델도 이상치 판단 시)
        # if deployed_lowest_model and deployed_lowest_model.predict(features.reshape(1, -1))[0] == -1:
        #    print("  - 최저 성능 모델도 이상치로 재확인됨.")
        #    # Alert 강도 높이기 등

        # 09:00 ~ 15:00 (주말/공휴일 제외) 인 경우 즉시 Alert/Report 트리거
        current_time = datetime.datetime.now().time()
        current_date = datetime.date.today()
        if is_weekday(current_date) and not is_holiday(current_date) and time(9, 0) <= current_time <= time(15, 0):
            print("  - 업무 시간 중 이상 탐지. 즉시 Alert/Report 트리거.")
            trigger_immediate_anomaly_alert(data_record, ensemble_score) # 즉시 Alert Worker 호출
            generate_immediate_anomaly_report(data_record, ensemble_score) # 즉시 보고서 Worker 호출
        else:
            print("  - 업무 시간 외 이상 탐지. 이상 결과 별도 기록 및 배치 보고에 포함.")
            log_anomaly_for_batch_report(data_record, ensemble_score) # 배치 보고용 로그 Worker 호출

    else:
        print("  - 이상 탐지되지 않음 (정상).")
        process_normal_realtime_record(data_record) # 정상 데이터 처리 및 요약 누적 Worker 호출

    print(">>> TainOn: 실시간 데이터 처리 완료 <<<")


# --- 배치 데이터 처리 및 이상 탐지 (TainBat 역할) ---

def schedule_daily_reporting_batch():
    """
    매일 05:00에 실행되도록 스케줄링된 함수 (주말/공휴일 제외).
    """
    current_date = datetime.date.today()
    if not is_weekday(current_date) or is_holiday(current_date):
         print(">>> 일별 보고 배치 스케줄: 주말/공휴일. 건너뛰기 <<<")
         return

    if datetime.datetime.now().time() == time(5, 0): # 실제 스케줄러는 정확한 시간에 트리거
        print(">>> 일별 보고 배치 스케줄 시작 (05:00) <<<")
        reporting_date = current_date - datetime.timedelta(days=1) # 전일 데이터 보고

        # 1. 전일 처리된 모든 트랜잭션 데이터 조회 (정상 + 이상 결과)
        all_transactions = retrieve_all_transactions_for_date(reporting_date) # DB 조회 Worker 호출

        if not all_transactions:
            print(f"  - 전일({reporting_date}) 처리된 트랜잭션 없음. 보고서 생성 건너뛰기.")
            return

        # 2. KTFC 보고서 형식으로 변환 및 파일 생성
        ktfc_report_content = generate_ktfc_report_format(all_transactions) # 보고서 형식 변환 Worker 호출

        # 3. KTFC 보고 시스템 전송
        send_report_to_ktfc(ktfc_report_content) # KTFC 전송 Worker 호출

        print(">>> 일별 보고 배치 스케줄 완료 <<<")


def batch_process_data_chunk(batch_data_features, batch_data_records, deployed_models):
     """
     TainBat가 배치 데이터를 처리할 때 데이터 청크별로 호출될 수 있는 함수.
     :param batch_data_features: 배치 데이터 특징 (NumPy 배열)
     :param batch_data_records: 배치 데이터 원본 레코드 목록
     :param deployed_models: 배포된 모델 딕셔너리
     """
     print(f"\n--- TainBat: 배치 청크 이상 탐지 시작 ({batch_data_features.shape[0]}개 데이터) ---")
     if deployed_models is None or not deployed_models:
          print("  - 모델 로딩 안됨. 이상 탐지 건너뛰고 정상 배치 처리.")
          # TODO: 모델 로딩 실패 알림 및 정상 배치 처리 로직
          process_normal_batch_records(batch_data_records)
          return

     # 1. 앙상블 모델로 이상치 평가
     ensemble_scores = deployed_models['EnsembleAnomalyDetector'].decision_function(batch_data_features)
     ensemble_predictions = deployed_models['EnsembleAnomalyDetector'].predict(batch_data_features)

     anomalous_indices_in_chunk = np.where(ensemble_predictions == -1)[0].tolist()

     # 2. 이상 탐지 결과 기반 처리
     if anomalous_indices_in_chunk:
         print(f"  - 배치 청크에서 이상 탐지됨: {len(anomalous_indices_in_chunk)}개")
         # TODO: 재확인 로직 필요 시 (예: 최저 성능 모델도 이상치 판단 시)

         # 이상 탐지된 데이터에 대해 Alert 및 Report 트리거 (09~15시 조건은 일별 보고 시 적용 가능)
         # 배치 처리 중에는 일단 이상 결과를 기록하고, 일별 보고 시 조건부 Alert/Report를 수행할 수도 있음.
         # 여기서는 배치 처리 완료 후 이상 데이터 목록을 모아 처리한다고 가정.
         anomalous_records_in_chunk = [batch_data_records[i] for i in anomalous_indices_in_chunk]
         log_anomalies_for_batch_report(anomalous_records_in_chunk, ensemble_scores[anomalous_indices_in_chunk]) # 배치 보고용 로그 Worker 호출

     else:
         print("  - 배치 청크 이상 없음.")
         process_normal_batch_records(batch_data_records) # 정상 배치 처리 및 집계


# --- 누적 보고서 작성 스케줄 (보고서 작성 서비스) ---

def schedule_cumulative_reports():
    """
    분기별, 반기별, 연간 누적 보고서 스케줄링 함수.
    """
    current_date = datetime.date.today()

    # 분기별 보고 (예: 3, 6, 9, 12월 말일)
    if current_date.month in [3, 6, 9, 12] and is_last_day_of_month(current_date):
        print(f">>> 분기별 누적 보고서 스케줄 시작 ({current_date}) <<<")
        generate_cumulative_anomaly_report('quarterly', current_date) # 보고서 Worker 호출

    # 반기별 보고 (예: 6, 12월 말일) - 분기별 보고 후 순차적으로
    if current_date.month in [6, 12] and is_last_day_of_month(current_date):
        print(f">>> 반기별 누적 보고서 스케줄 시작 ({current_date}) <<<")
        # 분기별 보고서 완료를 기다리거나 별도 트리거
        generate_cumulative_anomaly_report('semiannual', current_date) # 보고서 Worker 호출

    # 연간 보고 (예: 12월 말일) - 반기별 보고 후 순차적으로
    if current_date.month == 12 and is_last_day_of_month(current_date):
        print(f">>> 연간 누적 보고서 스케줄 시작 ({current_date}) <<<")
        # 반기별 보고서 완료를 기다리거나 별도 트리거
        generate_cumulative_anomaly_report('annual', current_date) # 보고서 Worker 호출


# --- Alert 및 Report Worker 함수 (개념적) ---

def trigger_immediate_anomaly_alert(data_record, score):
    """이상 탐지 시 즉시 알림/푸시를 발송하는 함수."""
    print(f"  [ALERT] 즉시 알림 발송: 레코드 {data_record.get('UNIQUE_ID')}, 이상치 점수 {score:.4f}")
    # TODO: 알림 시스템 API 호출 (SMS, 메신저, 푸시)

def generate_immediate_anomaly_report(data_record, score):
    """이상 탐지 시 즉시 상세 보고서를 작성/보관하는 함수."""
    print(f"  [REPORT] 즉시 이상 거래 보고서 작성 및 보관: 레코드 {data_record.get('UNIQUE_ID')}, 점수 {score:.4f}")
    # TODO: 보고서 형식에 맞게 데이터 기록, 파일 저장, DB 저장 등

def log_anomaly_for_batch_report(data_records, scores):
    """배치 보고서에 포함될 이상 데이터를 기록하는 함수."""
    print(f"  [LOG] 배치 보고서용 이상 데이터 기록: {len(data_records)}개")
    # TODO: 별도 테이블 또는 로그 파일에 이상 데이터 기록 (일별 보고 시 조회)

def generate_cumulative_anomaly_report(period, end_date):
    """누적 이상 데이터 보고서를 작성하는 함수."""
    print(f"  [REPORT] {period} 누적 이상 데이터 보고서 작성 및 보관 (기준일: {end_date})")
    # TODO: 누적 이상 데이터 DB 조회 -> 보고서 형식 변환 -> 파일/DB 저장

# --- 기타 유틸리티 함수 (개념적) ---

def preprocess_realtime_record(data_record):
     """실시간 레코드에서 특징 추출 및 전처리."""
     # TODO: 실제 구현 필요
     return np.array([data_record.get('Feature_1', 0), data_record.get('Feature_2', 0)])

def preprocess_batch_features(batch_data_features_raw):
      """배치 데이터 특징 전처리."""
      # TODO: 실제 구현 필요
      return batch_data_features_raw # 예시에서는 그대로 반환

def retrieve_all_transactions_for_date(date):
     """전일 처리된 모든 트랜잭션 (정상+이상)을 DB에서 조회."""
     print(f"  [DB] 전일({date}) 모든 트랜잭션 데이터 조회...")
     # TODO: DB 조회 로직 구현
     return [] # 예시에서는 빈 리스트 반환

def generate_ktfc_report_format(transactions):
      """트랜잭션 목록을 KTFC 보고 형식으로 변환."""
      print(f"  [REPORT] KTFC 보고서 형식 변환 ({len(transactions)}개 트랜잭션)...")
      # TODO: CFTC/KTFC 형식에 맞게 데이터 변환 및 파일 내용 생성 로직 구현
      return "KTFC_REPORT_CONTENT..." # 가상 보고서 내용

def send_report_to_ktfc(report_content):
      """KTFC 보고 시스템으로 보고서 전송 (Vo fep 역할)."""
      print("  [NETWORK] KTFC 보고 시스템으로 보고서 전송 시도...")
      # TODO: 파일 전송 (SFTP/SSH) 또는 API 호출 로직 구현

def process_normal_realtime_record(data_record):
     """정상 실시간 데이터를 처리하고 요약 누적."""
     print(f"  [NORMAL] 실시간 정상 데이터 처리 및 요약: 레코드 {data_record.get('UNIQUE_ID')}")
     # TODO: 데이터 저장, 집계, 요약 로직

def process_normal_batch_records(data_records):
      """정상 배치 데이터를 처리하고 집계."""
      print(f"  [NORMAL] 배치 정상 데이터 처리 및 집계: {len(data_records)}개")
      # TODO: 데이터 저장, 집계 로직

def get_latest_model_version(model_name):
     """모델 저장소에서 최신 모델 버전 조회."""
     # TODO: 모델 저장소 API 또는 DB 조회 로직 구현
     return "latest_version_simulated" # 가상 버전

def is_weekday(date):
     """주중인지 확인 (월~금)."""
     return date.weekday() < 5

def is_holiday(date):
     """공휴일인지 확인 (별도 공휴일 데이터 필요)."""
     # TODO: 공휴일 데이터베이스 또는 API 조회 로직 구현
     return False # 예시에서는 항상 False

def is_last_day_of_month(date):
    """월의 마지막 날인지 확인."""
    next_month = date.replace(day=28) + datetime.timedelta(days=4) # 다음달로 이동
    return date.day == (next_month - datetime.timedelta(days=next_month.day)).day

# --- 앙상블 모델 구성 (개념적) ---
def build_ensemble_tree(trained_individual_models, evaluation_features, evaluation_labels):
    """
    학습된 개별 모델들의 예측 결과를 조합하는 앙상블 트리 모델 학습.
    :param trained_individual_models: {모델 이름: 학습된 모델 객체} 딕셔너리
    :param evaluation_features: 평가 특징 데이터
    :param evaluation_labels: 평가 실제 라벨
    :return: 학습된 앙상블 모델 (예: scikit-learn DecisionTreeClassifier)
    """
    print("\n--- 앙상블 트리 모델 학습 시작 ---")
    if not trained_individual_models or evaluation_features is None or evaluation_labels is None:
        print("  - 앙상블 학습 데이터 또는 모델 부족. 앙상블 학습 건너뛰기.")
        return None

    # 개별 모델들의 예측 결과 (점수 또는 예측 라벨)를 수집
    ensemble_features = []
    model_names = list(trained_individual_models.keys())
    for name, model in trained_individual_models.items():
        try:
            # 이상치 점수를 앙상블 모델의 입력 특징으로 사용
            scores = model.decision_function(evaluation_features)
            ensemble_features.append(scores.reshape(-1, 1))
            print(f"  - {name} 예측 결과 수집 완료.")
        except Exception as e:
            print(f"  - {name} 예측 결과 수집 실패: {e}")
            # 실패한 모델의 결과는 제외 또는 대체값 사용

    if not ensemble_features:
         print("  - 수집된 개별 모델 예측 결과 없음. 앙상블 학습 실패.")
         return None

    # 개별 모델 예측 결과들을 하나의 특징 배열로 합침
    ensemble_input_features = np.hstack(ensemble_features) # Shape: num_samples x num_models

    # 앙상블 모델 (예: Decision Tree Classifier) 학습
    # 실제 라벨(evaluation_labels)을 사용하여 개별 모델 예측 결과를 보고 최종 이상치/정상 판단을 학습
    from sklearn.tree import DecisionTreeClassifier
    print("  - Decision Tree를 앙상블 모델로 학습...")
    # 평가 데이터셋의 라벨을 앙상블 모델 학습의 타겟으로 사용 (0: 정상, 1: 이상치)
    ensemble_target_labels = evaluation_labels # 실제 라벨 사용
    ensemble_classifier = DecisionTreeClassifier(random_state=42)
    ensemble_classifier.fit(ensemble_input_features, ensemble_target_labels)
    print("  - 앙상블 Decision Tree 모델 학습 완료.")


    # 앙상블 모델의 예측 함수를 원래 모델 객체에 추가하여 반환 (개념적)
    # 실제로는 앙상블 모델 자체를 새로운 클래스로 만들거나, 예측 파이프라인을 구성합니다.
    # 여기서는 학습된 Decision Tree를 예측에 사용하는 방식으로 시뮬레이션합니다.
    class EnsembleAnomalyPredictor:
        def __init__(self, individual_models, ensemble_classifier):
            self.individual_models = individual_models
            self.ensemble_classifier = ensemble_classifier

        def decision_function(self, X):
             # 개별 모델 점수 계산
             individual_scores = []
             for name, model in self.individual_models.items():
                 try:
                     score = model.decision_function(X)
                     individual_scores.append(score.reshape(-1, 1))
                 except Exception as e:
                     # 실패한 모델은 특정 값 (예: 0)으로 대체 또는 처리
                     print(f"  - 앙상블 예측 중 개별 모델({name}) 점수 계산 실패: {e}. 0으로 처리.")
                     individual_scores.append(np.zeros((X.shape[0], 1))) # 실패 시 0으로 채움

             if not individual_scores:
                  # 모든 개별 모델 예측 실패 시 오류 처리
                 print("  - 앙상블 예측 실패: 개별 모델 점수 계산 불가.")
                 # 오류 반환 또는 기본값 처리
                 return np.zeros(X.shape[0]) # 예시: 0점 반환

             ensemble_input_features = np.hstack(individual_scores)

             # 앙상블 분류기(Decision Tree)의 이상치 클래스 확률을 점수로 사용 (개념적)
             # Decision Tree의 predict_proba는 클래스별 확률 반환. 이상치(클래스 1) 확률 사용.
             # 확률이 높을수록 이상치이므로 점수에 -를 붙여 이상치 점수화
             anomaly_prob = self.ensemble_classifier.predict_proba(ensemble_input_features)[:, 1] # 이상치 클래스 (1)의 확률
             return -anomaly_prob # 확률이 높을수록 점수가 낮아짐 (이상치 경향)


        def predict(self, X):
            # decision_function 결과 기반으로 임계값 적용 (-1 또는 1)
            # 앙상블 분류기(Decision Tree)의 최종 예측 결과 사용
            individual_scores = []
            for name, model in self.individual_models.items():
                try:
                    score = model.decision_function(X)
                    individual_scores.append(score.reshape(-1, 1))
                except Exception as e:
                     print(f"  - 앙상블 예측 중 개별 모델({name}) 점수 계산 실패: {e}. 0으로 처리.")
                     individual_scores.append(np.zeros((X.shape[0], 1))) # 실패 시 0으로 채움

            if not individual_scores:
                 print("  - 앙상블 예측 실패: 개별 모델 점수 계산 불가.")
                 # 오류 반환 또는 기본값 처리
                 return np.ones(X.shape[0]) # 예시: 정상(1)으로 판단

            ensemble_input_features = np.hstack(individual_scores)
            final_prediction = self.ensemble_classifier.predict(ensemble_input_features) # 0 또는 1

            # 앙상블 분류기의 예측 결과(0: 정상, 1: 이상치)를 -1 또는 1로 변환
            return np.where(final_prediction == 1, -1, 1) # 1(이상치) -> -1, 0(정상) -> 1

    # 학습된 개별 모델과 학습된 Decision Tree를 포함하는 앙상블 예측 객체 생성
    ensemble_predictor = EnsembleAnomalyPredictor(trained_individual_models, ensemble_classifier)

    print("--- 앙상블 트리 모델 구성 완료 ---")
    return ensemble_predictor

# --- 날짜 및 시간 유틸리티 함수 (개념적) ---
import datetime
from datetime import date, time, timedelta

def get_last_week_date_range():
    """지난 주 월요일 0시부터 일요일 23:59까지의 날짜 범위 반환."""
    today = datetime.date.today()
    last_sunday = today - datetime.timedelta(days=today.weekday() + 1)
    last_monday = last_sunday - datetime.timedelta(days=6)
    return datetime.datetime.combine(last_monday, time.min), datetime.datetime.combine(last_sunday, time.max)

def load_evaluation_dataset():
    """모델 평가를 위한 라벨링된 별도의 평가 데이터셋 로딩."""
    print("\n--- 평가 데이터셋 로딩 시작 ---")
    # TODO: 실제 라벨링된 평가 데이터셋 로딩 로직 구현 (DB, 파일 등)
    # 이 데이터는 load_and_preprocess_swap_data에서 생성하는 가상 데이터와는 별개여야 함.
    # 여기서는 예시를 위해 load_and_preprocess_swap_data를 재사용하고 라벨 포함해서 반환
    features_eval, labels_eval = load_and_preprocess_swap_data(num_samples=500) # 500개 평가 데이터 가정
    print(f"--- 평가 데이터셋 로딩 완료 ({features_eval.shape[0]}개 데이터) ---")
    return features_eval, labels_eval

# TODO: is_holiday 함수 실제 구현 필요 (공휴일 데이터 기반)

# --- 메인 워크플로우 실행 예시 (스케줄 시뮬레이션) ---

if __name__ == "__main__":
    # --- 주간 모델 학습 및 업데이트 스케줄 시뮬레이션 ---
    print("\n#############################################")
    print("# 주간 모델 업데이트 스케줄 시뮬레이션 #")
    print("#############################################")
    schedule_weekly_model_update()


    # --- 일별 보고 배치 스케줄 시뮬레이션 ---
    print("\n#############################################")
    print("# 일별 보고 배치 스케줄 시뮬레이션 #")
    print("#############################################")
    # 실제 스케줄러는 매일 05시에 이 함수를 호출
    schedule_daily_reporting_batch()


    # --- 실시간 데이터 처리 및 이상 탐지 시뮬레이션 ---
    print("\n#############################################")
    print("# 실시간 데이터 처리 및 이상 탐지 시뮬레이션 #")
    print("#############################################")
    # TainOn 서비스 시작 또는 모델 업데이트 후 모델 로딩
    load_current_deployed_models()

    if deployed_ensemble_model:
        # TainTube로부터 데이터가 들어올 때마다 process_realtime_swap_data 호출 시뮬레이션
        sample_realtime_records = [
            {'UNIQUE_ID': 'LIVE_001', 'Feature_1': 5.2, 'Feature_2': 4.8}, # 정상 예상
            {'UNIQUE_ID': 'LIVE_002', 'Feature_1': 70.0, 'Feature_2': -3.0}, # 이상치 예상 (업무 시간 시뮬레이션)
            {'UNIQUE_ID': 'LIVE_003', 'Feature_1': 1.1, 'Feature_2': 0.9}, # 정상 예상
             {'UNIQUE_ID': 'LIVE_004', 'Feature_1': 80.0, 'Feature_2': 90.0}, # 이상치 예상 (업무 시간 외 시뮬레이션)
        ]
        # 현재 시간을 업무 시간 (예: 10시)으로 설정하여 시뮬레이션
        original_datetime_now = datetime.datetime.now # 실제 datetime.now 함수 저장
        def mock_datetime_now_business_hours():
             return datetime.datetime.combine(datetime.date.today(), time(10, 0)) # 업무 시간 중 시간 반환
        datetime.datetime.now = mock_datetime_now_business_hours # datetime.now 함수를 mock 함수로 대체

        for record in sample_realtime_records:
            process_realtime_swap_data(record)

        # datetime.now 함수 복원
        datetime.datetime.now = original_datetime_now
    else:
         print("배포된 앙상블 모델이 없어 실시간 탐지 시뮬레이션을 수행할 수 없습니다.")


    # --- 배치 데이터 이상 탐지 시뮬레이션 (TainBat 역할) ---
    print("\n#############################################")
    print("# 배치 데이터 이상 탐지 시뮬레이션 #")
    print("#############################################")
    if deployed_ensemble_model:
        # TainBat 배치 처리 시 데이터 청크 로딩 및 처리 시뮬레이션
        sample_batch_features = np.array([
            [4.0, 4.0], # 정상
            [88.0, 5.0], # 이상치
            [1.5, 1.8], # 정상
            [5.5, -1.0], # 이상치
        ])
        sample_batch_records = [{'ID': f'BATCH_{i}', 'Feature_1': sample_batch_features[i, 0], 'Feature_2': sample_batch_features[i, 1]} for i in range(sample_batch_features.shape[0])]

        batch_process_data_chunk(sample_batch_features, sample_batch_records, deployed_models={'EnsembleAnomalyDetector': deployed_ensemble_model})
    else:
         print("배포된 앙상블 모델이 없어 배치 탐지 시뮬레이션을 수행할 수 없습니다.")

    # --- 누적 보고서 스케줄 시뮬레이션 ---
    print("\n#############################################")
    print("# 누적 보고서 스케줄 시뮬레이션 #")
    print("#############################################")
    # 실제 스케줄러는 특정 날짜에 schedule_cumulative_reports 호출
    # 예: 3월 31일 시뮬레이션 (분기, 반기, 연간 보고 기준일 중 하나)
    # is_last_day_of_month 및 is_holiday 함수가 실제 날짜로 작동해야 함.
    # 여기서는 직접 호출 예시
    # current_date = date(2025, 3, 31) # 특정 날짜 설정
    # if is_last_day_of_month(current_date) and is_weekday(current_date) and not is_holiday(current_date):
    #      schedule_cumulative_reports()
    print("-> 누적 보고서 스케줄은 특정 월/일/요일/공휴일 조건에 따라 트리거됩니다.")
    print("-> 예시 코드는 스케줄러가 해당 함수를 호출하는 시점을 시뮬레이션합니다.")
