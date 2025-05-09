import numpy as np
import random
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# --- Worker 함수 1: 데이터 로딩 및 전처리 ---
# 실제 시스템에서는 DB나 파일에서 데이터를 읽어와 전처리합니다.
def load_and_preprocess_swap_data(num_samples=1000):
    """
    가상 스왑 거래 데이터 로딩 및 전처리 함수.
    이상치 샘플을 일부 포함하여 생성합니다.
    """
    print(f"--- 데이터 로딩 및 전처리 시작 (가상 데이터 {num_samples}개 생성) ---")

    # 가상 특징 데이터 (예: Notional Value, Variation Margin Ratio, Trading Frequency Index 등)
    # 정상 데이터 패턴: Feature_1, Feature_2가 특정 범위 내에 있음
    features = np.random.rand(num_samples, 2) * 10 # 0부터 10 사이의 랜덤 값 (Shape: 1000x2)

    # 가상 이상치 데이터 생성 (전체 데이터의 약 5%)
    num_anomalies = int(num_samples * 0.05)
    anomaly_indices = random.sample(range(num_samples), num_anomalies) # 이상치를 포함할 인덱스

    # 이상치 특징 생성 (정상 범위에서 벗어나는 값)
    for i in anomaly_indices:
        features[i, 0] = np.random.rand() * 100 + 20 # 비정상적으로 큰 값
        features[i, 1] = np.random.rand() * -5 # 비정상적으로 작은 값 또는 음수 값

    # 실제 데이터 라벨 (이상치 여부) - Isolation Forest는 비지도 학습 기반이므로,
    # 학습 시에는 라벨을 사용하지 않지만, 평가를 위해 라벨을 생성합니다.
    labels = np.zeros(num_samples, dtype=int) # 0: 정상
    labels[anomaly_indices] = 1 # 1: 이상치

    print(f"--- 데이터 로딩 완료: 정상 {num_samples - num_anomalies}개, 이상치 {num_anomalies}개 ---")
    # print("데이터 예시 (Features):", features[:5])
    # print("라벨 예시:", labels[:5])

    return features, labels

# --- Worker 함수 2: 이상치 탐지 모델 학습 ---
# 전처리된 데이터를 사용하여 이상치 탐지 모델을 학습합니다.
def train_anomaly_detection_model(X_train, contamination_rate=0.05):
    """
    Isolation Forest 모델 학습 함수.
    :param X_train: 학습 특징 데이터 (이상치 라벨은 학습에 사용되지 않음)
    :param contamination_rate: 데이터에서 이상치가 차지하는 비율 (모델 파라미터)
    :return: 학습된 Isolation Forest 모델
    """
    print(f"\n--- 이상치 탐지 모델 학습 시작 (Isolation Forest) ---")
    print(f"학습 데이터 개수: {X_train.shape[0]}, 특징 개수: {X_train.shape[1]}")
    print(f"예상 이상치 비율 (contamination): {contamination_rate}")

    # Isolation Forest 모델 초기화 및 학습
    # contamination 파라미터는 예상되는 이상치 비율을 알려주어 모델 성능 향상에 도움을 줍니다.
    # random_state를 고정하여 결과 재현 가능하도록 설정
    model = IsolationForest(contamination=contamination_rate, random_state=42)
    model.fit(X_train)

    print("--- 모델 학습 완료 ---")
    return model

# --- Worker 함수 3: 모델 평가 ---
# 학습되지 않은 테스트 데이터를 사용하여 모델 성능을 평가합니다.
def evaluate_model(model, X_test, y_test):
    """
    학습된 모델 성능 평가 함수.
    :param model: 학습된 모델
    :param X_test: 테스트 특징 데이터
    :param y_test: 테스트 실제 라벨
    """
    print(f"\n--- 모델 평가 시작 ---")
    print(f"평가 데이터 개수: {X_test.shape[0]}")

    # 테스트 데이터에 대한 이상치 점수 계산 (-1: 이상치, 1: 정상)
    # decision_function은 이상치 정도를 나타내는 점수를 반환합니다.
    # predict는 decision_function 결과에 contamination 임계값을 적용하여 -1 또는 1을 반환합니다.
    y_pred = model.predict(X_test)

    # Isolation Forest의 predict 결과(-1: 이상치, 1: 정상)를 실제 라벨(1: 이상치, 0: 정상)과 비교하기 위해 변환
    # -1 -> 1 (이상치), 1 -> 0 (정상)
    y_pred_binary = np.where(y_pred == -1, 1, 0)

    print("\n혼동 행렬 (Confusion Matrix):")
    print(confusion_matrix(y_test, y_pred_binary)) # 실제 라벨(y_test) vs 예측 라벨(y_pred_binary)

    print("\n분류 보고서 (Classification Report):")
    print(classification_report(y_test, y_pred_binary, target_names=['정상 (0)', '이상치 (1)']))

    print("--- 모델 평가 완료 ---")

# --- Worker 함수 4: 새로운 데이터에 대한 이상치 예측 ---
# 학습된 모델을 사용하여 실제 운영 중 발생하는 새로운 데이터의 이상치 여부를 예측합니다.
def predict_new_data(model, new_data_features):
    """
    새로운 데이터에 대한 이상치 예측 함수.
    :param model: 학습된 모델
    :param new_data_features: 예측할 새로운 데이터 특징
    :return: 각 데이터 샘플의 이상치 점수 및 예측 라벨 (-1: 이상치, 1: 정상)
    """
    print(f"\n--- 새로운 데이터 이상치 예측 시작 ---")
    print(f"예측 대상 데이터 개수: {new_data_features.shape[0]}")

    # 이상치 점수 계산 (-1에 가까울수록 이상치 경향)
    scores = model.decision_function(new_data_features)

    # 이상치 예측 라벨 (-1: 이상치, 1: 정상)
    predictions = model.predict(new_data_features)

    print("--- 예측 결과 (점수 및 라벨) ---")
    for i in range(new_data_features.shape[0]):
        print(f"데이터 {i+1}: 특징 [{new_data_features[i, 0]:.2f}, {new_data_features[i, 1]:.2f}], 이상치 점수: {scores[i]:.4f}, 예측 라벨: {'이상치' if predictions[i] == -1 else '정상'}")

    return scores, predictions

# --- 메인 실행 흐름 ---
if __name__ == "__main__":
    # 1. 데이터 로딩 및 전처리 Worker 호출
    features, labels = load_and_preprocess_swap_data(num_samples=2000) # 데이터 개수 늘림

    # 학습 데이터와 테스트 데이터 분리 (모델 성능 평가용)
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.3, random_state=42)

    # 2. 이상치 탐지 모델 학습 Worker 호출
    anomaly_model = train_anomaly_detection_model(X_train, contamination_rate=0.05)

    # 3. 모델 평가 Worker 호출
    # evaluate_model(anomaly_model, X_test, y_test) # 실제 이상치 라벨이 있는 경우 평가 가능

    # 4. 새로운 데이터 생성 및 예측 Worker 호출
    # 실제 운영에서는 DB나 스트림에서 새로운 데이터가 들어옵니다.
    new_live_data = np.array([
        [5.0, 5.5], # 정상 범위 데이터 예상
        [0.1, 0.2], # 정상 범위 데이터 예상
        [50.0, -1.0], # 이상치 데이터 예상
        [6.0, 7.0],  # 정상 범위 데이터 예상
        [120.0, 80.0], # 이상치 데이터 예상
    ])
    predict_new_data(anomaly_model, new_live_data)
