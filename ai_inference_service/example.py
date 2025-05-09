import numpy as np
import random # 가상 데이터 생성을 위해

# --- 1. 가상 스왑 거래 데이터 생성 ---
# 실제 데이터는 DB나 파일에서 로딩됩니다.
# 여기서는 Feature_1과 Feature_2라는 두 가지 숫자 특징과 Label(0 또는 1)을 가진 거래 데이터를 만듭니다.
# 패턴: Feature_1 + Feature_2 값이 특정 기준(예: 3.0)보다 크면 Label 1, 작으면 Label 0일 확률이 높다고 가정합니다.

num_samples = 1000 # 가상 거래 데이터 개수
features = np.random.rand(num_samples, 2) * 5 # 0부터 5 사이의 랜덤 값 (Shape: 1000x2)
labels = np.zeros(num_samples) # 라벨 초기화 (Shape: 1000)

# 가상 패턴에 따라 라벨 설정
for i in range(num_samples):
    # Feature_1 + Feature_2가 3.0보다 크면 Label 1, 아니면 0 (약간의 노이즈 추가)
    if features[i, 0] + features[i, 1] + random.uniform(-1, 1) > 3.5: # 노이즈를 포함한 기준
        labels[i] = 1
    else:
        labels[i] = 0

print(f"--- 가상 스왑 거래 데이터 생성 완료 (샘플 {num_samples}개) ---")
print("첫 5개 데이터 (Feature_1, Feature_2, Label):")
for i in range(5):
    print(f"[{features[i, 0]:.2f}, {features[i, 1]:.2f}], Label: {int(labels[i])}")

# --- 2. 단순 인공 신경망 모델 정의 (개념적) ---
# 입력층(2개 뉴런) -> 출력층(1개 뉴런, 시그모이드 활성화)
# 모델의 학습 대상은 '가중치(weights)'와 '편향(bias)'입니다.

input_size = 2  # Feature 개수
output_size = 1 # Label 개수

# 모델 파라미터 초기화 (무작위 값)
# 가중치 (weights): 각 입력 특징이 결과에 미치는 영향 (Shape: input_size x output_size)
weights = np.random.randn(input_size, output_size) * 0.01
# 편향 (bias): 입력과 무관한 기본적인 값 (Shape: 1 x output_size)
bias = np.zeros((1, output_size))

print("\n--- 모델 파라미터 초기값 ---")
print("Weights:\n", weights)
print("Bias:\n", bias)

# --- 3. 학습 과정 (패턴 파악 및 파라미터 조정) ---
# 경사 하강법(Gradient Descent)을 사용하여 오차를 줄이는 방향으로 weights와 bias를 조금씩 조정합니다.

learning_rate = 0.1 # 한 번 학습 시 파라미터 조정 폭
num_epochs = 100 # 전체 데이터셋을 반복 학습할 횟수

print("\n--- 학습 시작 ---")

for epoch in range(num_epochs):
    # 순전파 (Forward Pass): 입력 데이터를 모델에 통과시켜 예측값 계산
    # 예측값 = 입력 데이터 * 가중치 + 편향
    linear_output = np.dot(features, weights) + bias # Shape: num_samples x output_size

    # 시그모이드 활성화 함수: 예측값을 0과 1 사이 값으로 변환 (분류 문제에 적합)
    # 시그모이드(x) = 1 / (1 + exp(-x))
    predictions = 1 / (1 + np.exp(-linear_output)) # Shape: num_samples x output_size

    # 손실 계산 (Loss Calculation): 모델의 예측값과 실제 라벨 간의 오차 측정
    # 여기서는 간단한 평균 제곱 오차(Mean Squared Error)를 사용합니다.
    # MSE = 평균( (실제값 - 예측값)^2 )
    loss = np.mean((labels.reshape(-1, 1) - predictions) ** 2) # 라벨 Shape을 prediction과 맞춤

    # 역전파 (Backward Pass - 개념적): 손실을 줄이기 위해 weights와 bias를 얼마나 조정해야 하는지 계산 (기울기 계산)
    # 실제 역전파는 복잡하지만, 여기서는 MSE 손실에 대한 최종 출력의 기울기를 간략히 계산합니다.
    # dLoss/dPrediction = 2 * (Prediction - Actual) / num_samples
    # dPrediction/dLinearOutput = Prediction * (1 - Prediction) (시그모이드 미분)
    # dLoss/dLinearOutput = dLoss/dPrediction * dPrediction/dLinearOutput
    # dLoss/dWeights = 입력 데이터 전치행렬 * dLoss/dLinearOutput
    # dLoss/dBias = dLoss/dLinearOutput 의 합계

    gradient_prediction = 2 * (predictions - labels.reshape(-1, 1)) / num_samples
    gradient_linear_output = gradient_prediction * predictions * (1 - predictions) # 시그모이드 미분 적용

    gradient_weights = np.dot(features.T, gradient_linear_output) # Shape: input_size x output_size
    gradient_bias = np.sum(gradient_linear_output, axis=0, keepdims=True) # Shape: 1 x output_size

    # 파라미터 업데이트 (Parameter Update): 계산된 기울기(gradient)를 사용하여 weights와 bias 조정
    # 새로운 파라미터 = 현재 파라미터 - 학습률 * 기울기
    weights -= learning_rate * gradient_weights
    bias -= learning_rate * gradient_bias

    # 학습 과정 출력
    if (epoch + 1) % 10 == 0: # 10 에포크마다 손실과 파라미터 출력
        print(f"Epoch {epoch + 1}/{num_epochs}, Loss: {loss:.4f}")
        print("Updated Weights:\n", weights)
        print("Updated Bias:\n", bias)

print("\n--- 학습 완료 ---")
print("최종 모델 파라미터:")
print("Weights:\n", weights)
print("Bias:\n", bias)

# --- 4. 학습된 모델로 예측 (예시) ---
# 새로운 가상 데이터에 대해 예측을 수행해 봅니다.
new_features = np.array([[1.0, 1.2], [4.0, 3.5], [2.0, 3.0]]) # 새로운 가상 입력 데이터

# 순전파 과정 재사용
new_linear_output = np.dot(new_features, weights) + bias
new_predictions = 1 / (1 + np.exp(-new_linear_output)) # 시그모이드 통과

print("\n--- 새로운 데이터에 대한 예측 ---")
for i in range(new_features.shape[0]):
    predicted_category = 1 if new_predictions[i, 0] > 0.5 else 0 # 0.5 임계값으로 분류
    print(f"입력: [{new_features[i, 0]:.2f}, {new_features[i, 1]:.2f}], 예측 확률(Label 1): {new_predictions[i, 0]:.4f}, 예측 카테고리: {predicted_category}")
