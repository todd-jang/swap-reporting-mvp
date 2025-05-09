import numpy as np
import random
import time
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score, roc_curve
import joblib # 모델 저장을 위해
import os # 파일 경로 처리를 위해

# 간단한 Autoencoder를 위한 라이브러리 (실제로는 TensorFlow/PyTorch 사용)
# 여기서는 scikit-learn 호환 형태로 구현되거나, 라이브러리 호출을 모방합니다.
# 실제 Autoencoder는 신경망 모델이며 학습 방식이 IsolationForest/OneClassSVM과 다릅니다.
# 여기서는 개념적인 Fit/Predict 인터페이스만 모방합니다.
class SimpleAutoencoderAnomalyDetector:
    def __init__(self, encoding_dim=2, random_state=None):
        self.encoding_dim = encoding_dim
        self.random_state = random_state # 실제 학습에서는 더 복잡한 초기화 및 학습 로직 필요
        self.weights = None # 개념적 가중치

    def fit(self, X):
        print("  - SimpleAutoencoder 모델 학습 시뮬레이션...")
        # 실제로는 신경망 학습 알고리즘 (경사 하강법)으로 X를 사용하여 가중치(self.weights) 학습
        # 여기서는 학습된 가중치가 입력 특징의 평균과 표준편차에 기반한다고 '가정'합니다.
        self.feature_mean = np.mean(X, axis=0)
        self.feature_std = np.std(X, axis=0)
        # 매우 단순화된 예시이며, 실제 오토인코더 학습과 다릅니다.
        self.weights = np.random.randn(X.shape[1], self.encoding_dim) # 인코더 가중치 예시
        time.sleep(0.5) # 학습 시간 시뮬레이션
        print("  - SimpleAutoencoder 모델 학습 완료.")
        return self

    def predict(self, X):
        # 예측은 재구성 오차 기반 (이상치는 재구성 오차가 클 것)
        # 여기서는 특징이 평균에서 얼마나 벗어나는지로 이상치 여부 판단 (개념적)
        # 실제 오토인코더는 입력 -> 인코더 -> 디코더 -> 재구성된 입력 과정을 거쳐, 입력과 재구성된 입력 간의 오차를 계산합니다.
        reconstruction_error = np.sum(((X - self.feature_mean) / (self.feature_std + 1e-8))**2, axis=1) # 평균과의 차이 기반 오차 개념화
        # 오차 임계값은 학습 데이터의 오차 분포를 보고 결정 (예: 상위 N%)
        # 여기서는 임계값 5.0을 가정 (개념적)
        threshold = 5.0 # 개념적 임계값
        return np.where(reconstruction_error > threshold, -1, 1) # -1: 이상치, 1: 정상

    def decision_function(self, X):
        # 이상치 점수 반환 (점수가 낮을수록 이상치 경향)
        reconstruction_error = np.sum(((X - self.feature_mean) / (self.feature_std + 1e-8))**2, axis=1)
        return -reconstruction_error # 오차가 클수록(음수값 커질수록) 이상치 경향 점수


# --- Worker 함수 1: 데이터 샘플링 및 로딩 ---
def sample_and_load_data(data_source_config, start_time, end_time, sample_rate="hourly"):
    """
    데이터 소스 설정 및 시간 범위에 따라 데이터를 샘플링하고 로딩하는 함수.
    :param data_source_config: 데이터베이스 연결 정보, 파일 경로 등
    :param start_time: 샘플링 시작 시간
    :param end_time: 샘플링 종료 시간
    :param sample_rate: 샘플링 주기 (예: "hourly", "daily")
    :return: 샘플링된 특징 데이터 (NumPy 배열)
    """
    print(f"\n--- 데이터 샘플링 및 로딩 시작 ({start_time} ~ {end_time}) ---")
    # TODO: 실제 DB 연결 또는 파일 시스템 접근 로직 구현
    # 예: 데이터베이스에서 WHERE절로 시간 범위 및 샘플링 조건 적용하여 데이터 조회
    # 예: file_access.read_swap_data_by_time_range(data_source_config['path'], start_time, end_time, sample_rate)

    # 가상 데이터 샘플링 시뮬레이션
    num_samples_per_interval = 50 # 시간당 샘플 개수 가정
    total_intervals = int((end_time - start_time).total_seconds() / (3600 if sample_rate == "hourly" else 86400)) # 시간 간격 수 계산
    if total_intervals <= 0: total_intervals = 1

    total_samples = num_samples_per_interval * total_intervals
    features = np.random.rand(total_samples, 2) * 10 # 정상 데이터 범위
    print(f"  - 총 {total_samples}개 샘플링 완료 (가상).")

    # 가상 이상치 추가 (샘플링된 데이터의 일부에)
    num_anomalies_in_sample = int(total_samples * 0.03) # 샘플 데이터 중 이상치 비율 가정
    anomaly_indices = random.sample(range(total_samples), num_anomalies_in_sample)
    for i in anomaly_indices:
         features[i, 0] = np.random.rand() * 100 + 20
         features[i, 1] = np.random.rand() * -5

    print(f"--- 데이터 로딩 및 샘플링 완료 ({total_samples}개 데이터) ---")
    return features

# --- Worker 함수 2: 여러 이상치 탐지 모델 학습 ---
def train_multiple_anomaly_models(X_train, model_configs):
    """
    여러 종류의 이상치 탐지 모델을 학습하는 함수.
    :param X_train: 학습 특징 데이터
    :param model_configs: 각 모델별 설정 (이름, 파라미터 등)
    :return: {모델 이름: 학습된 모델 객체} 딕셔너리
    """
    print("\n--- 여러 이상치 탐지 모델 학습 시작 ---")
    trained_models = {}

    for config in model_configs:
        model_name = config['name']
        model_params = config.get('params', {})
        print(f"  - 모델 학습 중: {model_name}")

        try:
            if model_name == 'IsolationForest':
                model = IsolationForest(**model_params, random_state=42)
                model.fit(X_train)
            elif model_name == 'OneClassSVM':
                # OneClassSVM은 nu 파라미터가 중요 (이상치 비율의 상한)
                model = OneClassSVM(**model_params)
                model.fit(X_train)
            elif model_name == 'Autoencoder':
                # 개념적인 Autoencoder 모델 학습
                model = SimpleAutoencoderAnomalyDetector(**model_params, random_state=42)
                model.fit(X_train)
            else:
                print(f"  - 알 수 없는 모델 타입: {model_name}. 건너뜁니다.")
                continue

            trained_models[model_name] = model
            print(f"  - 모델 학습 완료: {model_name}")

        except Exception as e:
            print(f"  - 모델 학습 실패: {model_name}, 오류: {e}")
            # 실패한 모델은 결과에 포함하지 않음

    print("--- 전체 모델 학습 완료 ---")
    return trained_models

# --- Worker 함수 3: 모델 평가 및 비교 ---
def evaluate_and_compare_models(models, X_test, y_test):
    """
    학습된 모델들의 성능을 평가하고 비교 결과를 반환하는 함수.
    :param models: {모델 이름: 학습된 모델 객체} 딕셔너리
    :param X_test: 평가 특징 데이터
    :param y_test: 평가 실제 라벨 (비지도 학습 모델 평가를 위해 필요)
    :return: {모델 이름: 성능 지표 딕셔너리} 딕셔너리
    """
    print("\n--- 모델 평가 및 비교 시작 ---")
    comparison_results = {}

    # 비지도 학습 모델의 예측 결과(-1, 1)를 실제 라벨(0, 1)과 맞추는 도우미 함수
    def convert_predict_label(y_pred):
         return np.where(y_pred == -1, 1, 0) # -1(이상치) -> 1, 1(정상) -> 0

    for name, model in models.items():
        print(f"  - 모델 평가 중: {name}")
        try:
            # 예측 라벨 및 이상치 점수 계산
            y_pred = model.predict(X_test)
            anomaly_scores = model.decision_function(X_test)

            # 평가 지표 계산 (실제 라벨 y_test가 필요)
            y_pred_binary = convert_predict_label(y_pred)

            # 이상치 탐지에서는 Precision, Recall, F1-Score, ROC AUC 등이 중요
            # 특히 Recall (실제 이상치를 얼마나 잘 잡는지)과 Precision (이상치라고 예측한 것 중 실제 이상치 비율)의 균형이 중요
            # ROC AUC는 이상치 점수를 기준으로 분류 성능 평가
            auc_score = roc_auc_score(y_test, -anomaly_scores) # 점수가 낮을수록 이상치이므로 점수에 -를 붙여 AUC 계산

            metrics = {
                'precision': precision_score(y_test, y_pred_binary),
                'recall': recall_score(y_test, y_pred_binary),
                'f1_score': f1_score(y_test, y_pred_binary),
                'roc_auc': auc_score,
                # TODO: 필요시 다른 지표 추가 (예: confusion matrix 값)
            }
            comparison_results[name] = metrics
            print(f"  - 모델 평가 완료: {name}, ROC AUC: {auc_score:.4f}")

        except Exception as e:
            print(f"  - 모델 평가 실패: {name}, 오류: {e}")

    print("\n--- 모델 비교 결과 ---")
    # 성능 지표(예: ROC AUC) 기준으로 모델 순위 출력
    if comparison_results:
        # ROC AUC 기준으로 내림차순 정렬
        sorted_models = sorted(comparison_results.items(), key=lambda item: item[1].get('roc_auc', -1), reverse=True)
        for name, metrics in sorted_models:
             print(f"  - {name}: ROC AUC={metrics.get('roc_auc', -1):.4f}, Precision={metrics.get('precision', -1):.4f}, Recall={metrics.get('recall', -1):.4f}, F1-Score={metrics.get('f1_score', -1):.4f}")

    print("--- 모델 평가 및 비교 완료 ---")
    return comparison_results

# --- Worker 함수 4: 학습된 모델 저장 및 배포 ---
def save_and_deploy_model(model, model_name, version="latest"):
    """
    학습된 모델 객체를 파일로 저장하고 배포 위치로 복사하는 함수.
    :param model: 학습된 모델 객체
    :param model_name: 모델 이름
    :param version: 모델 버전 정보
    :return: 모델 파일 경로
    """
    print(f"\n--- 모델 저장 및 배포 시작: {model_name}, 버전: {version} ---")
    # TODO: 실제 모델 저장소 (Object Storage, 모델 관리 DB) 경로 사용
    model_dir = f"model_repository/{model_name}"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, f"{version}.joblib")

    try:
        # joblib을 사용하여 모델 객체를 파일로 저장
        joblib.dump(model, model_path)
        print(f"  - 모델 저장 완료: {model_path}")

        # TODO: 실제 배포 위치 (예: Object Storage 특정 버킷)로 파일 복사 또는 업로드 로직 추가
        # 예: upload_to_object_storage(model_path, f"models/{model_name}/{version}.joblib")

        print(f"--- 모델 저장 및 배포 완료: {model_name}, 경로: {model_path} ---")
        return model_path

    except Exception as e:
        print(f"  - 모델 저장 및 배포 실패: {model_name}, 오류: {e}")
        return None

# --- Worker 함수 5: 배포된 모델 로딩 ---
def load_deployed_model(model_name, version="latest"):
    """
    배포된 모델 파일을 로딩하여 모델 객체를 반환하는 함수.
    :param model_name: 모델 이름
    :param version: 로딩할 모델 버전 정보
    :return: 로딩된 모델 객체 또는 None
    """
    print(f"\n--- 모델 로딩 시작: {model_name}, 버전: {version} ---")
    # TODO: 실제 모델 저장소 (Object Storage, 모델 관리 DB) 경로 사용
    model_path = f"model_repository/{model_name}/{version}.joblib"

    # TODO: 실제 배포 위치에서 파일 다운로드 또는 접근 로직 추가
    # 예: download_from_object_storage(f"models/{model_name}/{version}.joblib", model_path)

    if not os.path.exists(model_path):
        print(f"  - 모델 파일 찾을 수 없음: {model_path}")
        return None

    try:
        # joblib을 사용하여 모델 객체를 파일에서 로딩
        model = joblib.load(model_path)
        print(f"  - 모델 로딩 완료: {model_name}")
        return model
    except Exception as e:
        print(f"  - 모델 로딩 실패: {model_name}, 오류: {e}")
        return None


# --- Worker 함수 6: 실시간 데이터 이상 탐지 및 Alert/Report ---
def realtime_anomaly_check(data_record, deployed_models):
    """
    실시간으로 들어오는 데이터 레코드의 이상치 여부를 탐지하고 필요시 Alert/Report를 트리거하는 함수.
    TainOn 구성 요소에서 호출될 수 있습니다.
    :param data_record: 실시간 데이터 레코드 (딕셔너리 또는 객체)
    :param deployed_models: {모델 이름: 로딩된 모델 객체} 딕셔너리 또는 특정 모델 객체
    """
    print(f"\n--- 실시간 이상 탐지 시작 (레코드: {data_record.get('UNIQUE_ID', 'N/A')}) ---")
    # TODO: 데이터 레코드에서 예측에 사용할 특징 추출 및 전처리 로직 구현
    # 예: features = preprocess_realtime_record(data_record)

    # 가상 특징 추출
    features = np.array([[data_record.get('Feature_1', 0), data_record.get('Feature_2', 0)]]) # Shape (1, n_features)

    anomaly_alerts = {}
    prediction_results = {}

    # 여러 모델로 이상치 예측 수행
    for model_name, model in deployed_models.items():
        try:
            # 이상치 점수 계산 (-1에 가까울수록 이상치)
            score = model.decision_function(features)[0]
            # 예측 라벨 (-1: 이상치, 1: 정상)
            prediction = model.predict(features)[0]

            is_anomaly = (prediction == -1)
            prediction_results[model_name] = {'score': score, 'prediction': '이상치' if is_anomaly else '정상'}

            if is_anomaly:
                # 이상 탐지 기준 초과 시 (예: 예측 라벨이 -1 또는 점수가 특정 임계값 이하)
                print(f"  - 이상 탐지됨 by {model_name}: 점수 {score:.4f}")
                anomaly_alerts[model_name] = score

        except Exception as e:
            print(f"  - 예측 실패 by {model_name}, 오류: {e}")
            prediction_results[model_name] = {'error': str(e)}


    # 이상 탐지 결과 기반 Alert 및 Report 트리거
    if anomaly_alerts:
        print("  - 이상 탐지 발생. Alert 및 Report 트리거.")
        # TODO: Alert 시스템 호출 (예: 이메일, SMS, 메신저 알림)
        # 예: trigger_alert_system(f"실시간 이상 탐지: 레코드 {data_record.get('UNIQUE_ID')}, 모델 결과: {anomaly_alerts}")
        # TODO: 이상 거래 보고서 작성 및 보관 로직 호출
        # 예: generate_anomaly_report(data_record, prediction_results)
        # TODO: 이상 거래는 정상 리포트에서 제외하거나 별도 관리

        return {"status": "anomaly_detected", "models_alerted": list(anomaly_alerts.keys()), "predictions": prediction_results}

    else:
        print("  - 이상 탐지되지 않음.")
        # TODO: 정상 거래 요약 리포트 작성 및 보관 (주기적으로)
        # 예: aggregate_normal_records(data_record) # 정상 데이터 집계 후 주기적으로 리포트 작성

        return {"status": "normal", "predictions": prediction_results}


# --- Worker 함수 7: 배치 데이터 이상 탐지 및 Alert/Report ---
def batch_anomaly_check(batch_data_features, deployed_models):
    """
    배치 데이터에 대한 이상치 여부를 탐지하고 필요시 Alert/Report를 트리거하는 함수.
    TainBat 구성 요소에서 호출될 수 있습니다.
    :param batch_data_features: 배치 특징 데이터 (NumPy 배열)
    :param deployed_models: {모델 이름: 로딩된 모델 객체} 딕셔너리
    """
    print(f"\n--- 배치 이상 탐지 시작 ({batch_data_features.shape[0]}개 데이터) ---")

    anomaly_indices_by_model = {}
    prediction_results_batch = {}

    # 여러 모델로 이상치 예측 수행
    for model_name, model in deployed_models.items():
        try:
            # 이상치 점수 계산 (-1에 가까울수록 이상치)
            scores = model.decision_function(batch_data_features)
            # 예측 라벨 (-1: 이상치, 1: 정상)
            predictions = model.predict(batch_data_features)

            is_anomaly_mask = (predictions == -1)
            anomaly_indices_by_model[model_name] = np.where(is_anomaly_mask)[0].tolist() # 이상치로 예측된 데이터의 배치 내 인덱스
            prediction_results_batch[model_name] = {'scores': scores, 'predictions': predictions} # 전체 결과 저장

            num_anomalies_detected = len(anomaly_indices_by_model[model_name])
            if num_anomalies_detected > 0:
                print(f"  - 이상 탐지됨 by {model_name}: {num_anomalies_detected}개 데이터")

        except Exception as e:
            print(f"  - 예측 실패 by {model_name}, 오류: {e}")
            prediction_results_batch[model_name] = {'error': str(e)}


    # 배치 이상 탐지 결과 기반 Alert 및 Report 트리거
    all_anomalous_indices = set()
    for indices in anomaly_indices_by_model.values():
        all_anomalous_indices.update(indices) # 여러 모델 중 하나라도 이상치로 탐지하면 포함

    if all_anomalous_indices:
        print(f"  - 배치에서 총 {len(all_anomalous_indices)}개 이상 거래 탐지. Alert 및 Report 트리거.")
        # TODO: 이상 탐지된 배치 데이터만 추출하여 상세 분석 또는 보고
        # anomalous_data = batch_data_features[list(all_anomalous_indices)]
        # TODO: Alert 시스템 호출 (예: 배치 이상 탐지 결과 요약 알림)
        # 예: trigger_alert_system(f"배치 이상 탐지 결과: {len(all_anomalous_indices)}개 데이터 이상 확인")
        # TODO: 배치 이상 거래 보고서 작성 및 보관 로직 호출
        # 예: generate_batch_anomaly_report(anomalous_data, prediction_results_batch)

        return {"status": "anomalies_detected_in_batch", "num_anomalies": len(all_anomalous_indices), "anomaly_indices": list(all_anomalous_indices)}

    else:
        print("  - 배치에서 이상 탐지된 데이터 없음.")
        return {"status": "batch_normal"}


# --- 모델 성능 최저 모델 재확인 (개념적) ---
# 요구사항: 모델별 성능 비교 후 최저 성능 모델을 최종 재확인시 사용
# 실제 운영에서는 보통 최고 성능 모델이나 앙상블 모델을 사용하지만,
# 여기서는 요청에 맞춰 성능 비교 결과를 바탕으로 최저 성능 모델을 식별하는 로직을 보여줍니다.
# 이 함수는 모델 학습 후 evaluate_and_compare_models 호출 뒤에 실행될 수 있습니다.
def identify_lowest_performing_model(comparison_results):
    """
    모델 비교 결과에서 성능 지표가 가장 낮은 모델을 식별합니다.
    :param comparison_results: {모델 이름: 성능 지표 딕셔너리} 딕셔너리
    :return: 최저 성능 모델 이름 또는 None
    """
    print("\n--- 최저 성능 모델 식별 ---")
    if not comparison_results:
        print("  - 비교 결과 없음.")
        return None

    lowest_model_name = None
    lowest_metric_value = float('inf') # 가장 낮은 값을 찾기 위해 무한대로 초기화

    # 어떤 지표로 최저 성능을 판단할지 기준 필요 (예: ROC AUC가 가장 낮은 모델)
    metric_to_compare = 'roc_auc' # ROC AUC가 낮을수록 성능이 안 좋다고 가정

    for name, metrics in comparison_results.items():
        metric_value = metrics.get(metric_to_compare, float('inf')) # 해당 지표 값, 없으면 무한대

        # ROC AUC는 높을수록 좋으므로, 가장 낮은 (즉, 가장 안 좋은) ROC AUC를 찾습니다.
        if metric_value < lowest_metric_value:
            lowest_metric_value = metric_value
            lowest_model_name = name

    if lowest_model_name:
        print(f"  - '{metric_to_compare}' 지표 기준 최저 성능 모델: {lowest_model_name} (값: {lowest_metric_value:.4f})")
    else:
        print("  - 최저 성능 모델 식별 실패.")

    return lowest_model_name

# --- 메인 워크플로우 (개념적) ---
# TainBat 스케줄러의 주기적 실행 또는 배치 처리에 해당
if __name__ == "__main__":
    print("--- AI 학습 및 배치 이상 탐지 워크플로우 시작 ---")

    # 워크플로우 파라미터
    data_config = {'db_conn': '...', 'path': '/data/swap_reports'} # 가상 데이터 소스 설정
    training_period_start = datetime.datetime.now() - datetime.timedelta(days=30) # 지난 30일 데이터 학습
    training_period_end = datetime.datetime.now()

    # 학습할 모델 설정
    model_configs_to_train = [
        {'name': 'IsolationForest', 'params': {'contamination': 0.05, 'n_estimators': 100}}, # n_estimators 트리 개수
        {'name': 'OneClassSVM', 'params': {'nu': 0.05, 'kernel': 'rbf', 'gamma': 'auto'}}, # nu 이상치 비율 상한, kernel/gamma는 SVM 커널 파라미터
        {'name': 'Autoencoder', 'params': {'encoding_dim': 2}}, # 개념적 Autoencoder 파라미터
    ]

    # 1. 데이터 샘플링 및 로딩 Worker 호출
    training_features = sample_and_load_data(data_config, training_period_start, training_period_end, sample_rate="daily")

    # 학습/평가 데이터 분리 (실제 라벨이 있는 경우 평가 가능)
    # 비지도 학습 모델 자체는 라벨 없이 fit하지만, 성능 평가를 위해 라벨 필요
    # 실제 운영 데이터에는 이상치 라벨이 없을 가능성이 높으므로, 평가 데이터셋은 별도로 구축된 라벨링된 데이터 사용하거나, 일부 데이터만 라벨링하여 사용
    # 여기서는 샘플링된 데이터의 라벨 (가상으로 생성한 것)을 사용하여 평가 시뮬레이션
    # TODO: 실제 환경에서는 라벨링된 별도의 평가 데이터셋 로딩
    features_with_labels, labels_for_eval = load_and_preprocess_swap_data(num_samples=500) # 별도 평가 데이터셋 가정
    X_train_eval, X_test_eval, y_train_eval, y_test_eval = train_test_split(features_with_labels, labels_for_eval, test_size=0.5, random_state=42)
    # 학습 데이터셋에서는 이상치 비율을 알 수 없다고 가정하고 fit
    # 평가 데이터셋에서는 라벨이 있다고 가정하고 evaluate

    # 2. 여러 이상치 탐지 모델 학습 Worker 호출
    trained_models = train_multiple_anomaly_models(training_features, model_configs_to_train)

    # 3. 모델 평가 및 비교 Worker 호출
    if trained_models:
        # 실제 라벨이 있는 평가 데이터셋으로 모델 평가
        comparison_results = evaluate_and_compare_models(trained_models, X_test_eval, y_test_eval)

        # 4. 모델 선택 및 배포
        # 실제로는 성능 지표(ROC AUC 등)가 가장 좋은 모델 또는 앙상블 모델을 선택
        # 여기서는 모든 학습된 모델을 일단 배포한다고 가정
        deployed_models = {}
        for name, model in trained_models.items():
            saved_path = save_and_deploy_model(model, name, version=time.strftime("%Y%m%d%H%M%S")) # 현재 시간을 버전으로 사용
            if saved_path:
                 # 배포된 모델을 로딩하여 사용 준비
                 loaded_model = load_deployed_model(name, version=os.path.basename(os.path.dirname(saved_path))) # 저장된 경로에서 버전 정보 추출
                 if loaded_model:
                     deployed_models[name] = loaded_model

        # 5. 모델 재확인용 최저 성능 모델 식별 (요청 사항 반영)
        if comparison_results:
            lowest_model_name = identify_lowest_performing_model(comparison_results)
            # TODO: 이 최저 성능 모델을 어떻게 '재확인'에 사용할지 로직 구현 필요
            # 예: 이상 탐지 시, 최저 성능 모델 결과도 함께 보여주어 참고하도록 하거나,
            #    최저 성능 모델도 '이상치'라고 판단한 경우에만 최종 Alert 강도를 높이는 등.

    else:
        print("\n학습된 모델이 없습니다. 워크플로우 종료.")
        deployed_models = {}


    # --- 실시간 이상 탐지 시뮬레이션 (TainOn 역할) ---
    print("\n--- 실시간 이상 탐지 시뮬레이션 ---")
    if deployed_models:
        live_records = [
            {'UNIQUE_ID': 'REC_001', 'Feature_1': 6.0, 'Feature_2': 4.5}, # 정상 예상
            {'UNIQUE_ID': 'REC_002', 'Feature_1': 55.0, 'Feature_2': -2.0}, # 이상치 예상
            {'UNIQUE_ID': 'REC_003', 'Feature_1': 8.0, 'Feature_2': 8.2}, # 정상 예상
        ]
        for record in live_records:
            realtime_anomaly_check(record, deployed_models) # 실시간 체크 Worker 호출

    else:
         print("배포된 모델이 없어 실시간 탐지를 수행할 수 없습니다.")


    # --- 배치 이상 탐지 시뮬레이션 (TainBat 역할) ---
    print("\n--- 배치 이상 탐지 시뮬레이션 ---")
    if deployed_models:
        # 배치 데이터 로딩 (가상)
        batch_data = np.array([
            [7.0, 7.0],   # 정상 예상
            [0.5, 0.8],   # 정상 예상
            [95.0, 10.0], # 이상치 예상
            [15.0, 16.0], # 정상 예상
            [1.0, -0.5],  # 이상치 예상
            [8.0, 8.5],   # 정상 예상
        ])
        batch_anomaly_check(batch_data, deployed_models) # 배치 체크 Worker 호출

    else:
        print("배포된 모델이 없어 배치 탐지를 수행할 수 없습니다.")


    # --- 정상 데이터 요약 리포트 작성 (TainBat 또는 TainOn 역할) ---
    # 실시간/배치 처리 과정에서 '정상'으로 분류된 데이터를 주기적으로 집계하여 리포트 작성
    # 이 부분은 이상 탐지 로직과 별개로, 정상 데이터 처리 흐름에 통합됩니다.
    # 예: TainBat가 매일 밤 '정상' 거래 데이터를 집계하여 일별 요약 보고서 작성

    print("\n--- AI 학습 및 배치 이상 탐지 워크플로우 종료 ---")
