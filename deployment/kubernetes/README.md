Deployment Steps:

Build and Push Docker Images: Ensure you have built Docker images for all your microservices and pushed them to a container registry accessible by your Kubernetes cluster. Update the image: fields in the Deployment manifests with the correct image names and tags.

Create Secrets: Create the swap-reporting-secrets Secret using kubectl create secret generic or by applying the YAML file (ensure sensitive data is base64 encoded). Be very careful not to expose your secrets.

# Example (replace with your actual values and encoding)
# kubectl create secret generic swap-reporting-secrets --from-literal=DATABASE_USER=your_db_user --from-literal=DATABASE_PASSWORD=your_db_password --from-literal=DATABASE_NAME=your_db_name --from-literal=AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID --from-literal=AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY --namespace swap-reporting

Apply ConfigMaps: Apply the configmaps.yaml file.

kubectl apply -f deployment/kubernetes/configmaps.yaml

Apply Database Manifests: Apply the database Deployment (StatefulSet) and Service manifests. If using a managed database service, skip this and ensure your DATABASE_URL in the ConfigMap points to the external service.

kubectl apply -f deployment/kubernetes/db-deployment.yaml
kubectl apply -f deployment/kubernetes/db-service.yaml

Apply Microservice Deployments and Services: Apply the Deployment and Service manifests for all your microservices.

kubectl apply -f deployment/kubernetes/data-ingestion-deployment.yaml
kubectl apply -f deployment/kubernetes/data-processing-deployment.yaml
kubectl apply -f deployment/kubernetes/validation-deployment.yaml
kubectl apply -f deployment/kubernetes/report-generation-deployment.yaml
kubectl apply -f deployment/kubernetes/report-submission-deployment.yaml
kubectl apply -f deployment/kubernetes/error-monitoring-deployment.yaml
kubectl apply -f deployment/kubernetes/web-deployment.yaml
kubectl apply -f deployment/kubernetes/services.yaml

Apply Ingress: If you have an Ingress Controller installed, apply the ingress.yaml file. Update the host field to your domain and ensure your DNS points to the Ingress Controller's IP.

kubectl apply -f deployment/kubernetes/ingress.yaml

Verify Deployment: Use kubectl get pods -n swap-reporting, kubectl get deployments -n swap-reporting, kubectl get services -n swap-reporting, kubectl get ingress -n swap-reporting to check the status of your deployed resources.

QnA

1. 여러 개의 마이크로서비스임에도 진입점은 하나인가?

네, 일반적으로 외부 사용자가 접근하는 진입점은 하나(API Gateway)로 하는 것이 마이크로서비스 아키텍처의 표준적인 패턴이며 권장되는 방식입니다.

왜 진입점은 하나인가?:

클라이언트 단순성: 웹 프론트엔드, 모바일 앱 또는 외부 시스템과 같은 클라이언트는 시스템에 접근하기 위해 단 하나의 URL (API Gateway의 URL)만 알면 됩니다. 백엔드에 어떤 마이크로서비스가 몇 개 있는지 몰라도 됩니다.
관심사 분리: 인증, 권한 부여 (부분적인), 로깅, 속도 제한, 부하 분산, 보안 (WAF, DDoS 방어) 등 클라이언트와 백엔드 서비스 전반에 걸쳐 필요한 공통 기능들을 API Gateway에서 중앙 집중식으로 처리할 수 있습니다. 각 마이크로서비스는 자신의 핵심 비즈니스 로직에만 집중할 수 있습니다.
백엔드 유연성: 백엔드의 마이크로서비스를 리팩토링하거나, 다른 기술 스택으로 교체하거나, 확장/축소하더라도 API Gateway 뒤에 숨겨져 있으므로 클라이언트에 영향을 주지 않습니다. API Gateway의 라우팅 설정만 변경하면 됩니다.
예외: 시스템 내부에서 마이크로서비스들끼리 통신할 때는 API Gateway를 거치지 않고 내부 네트워크를 통해 직접 통신하거나 내부 로드 밸런서, 서비스 메시를 통해 통신하는 것이 일반적입니다. 또한, 특정 시스템 관리나 모니터링 목적의 API는 API Gateway를 통하지 않고 별도의 내부 진입점을 가질 수도 있습니다. 하지만 외부 사용자의 '기능 접근' 진입점은 하나로 통합합니다.

여러분의 "swap-reporting-mvp" 아키텍처 다이어그램에서도 API Gateway가 외부와 API 서버들(Vb api svr, Vo api svr) 사이의 단일 진입점으로 표현되어 있습니다.

2. 클러스터에 VM 3개 이상 워커 노드면 우리 일괄전송시스템으로 충분한가?

Kubernetes 클러스터에 VM(워커 노드)이 3개 이상이라는 것은 고가용성을 확보하고 최소한의 자원을 제공하는 좋은 시작점입니다. 하지만 이것만으로 여러분의 일괄전송시스템(TainBat, 파일 I/O 등)을 포함한 시스템 전체가 충분한지는 단정적으로 말할 수 없습니다.

충분함의 기준: "충분하다"는 것은 다음을 의미합니다.

일괄전송시스템 Pod가 필요로 하는 **최대 자원(CPU, 메모리, 디스크 I/O, 네트워크 대역폭)**을 노드들이 제공할 수 있어야 합니다.
일괄전송시스템 Pod가 실행될 때, 다른 Pod들(API 서버, TainTube, TainOn, DB 등)이 필요로 하는 자원과 경합하지 않고도 모두 원활하게 작동할 수 있어야 합니다.
일괄전송시스템 배치 작업이 요구되는 처리 시간(성능) 내에 완료될 수 있어야 합니다.
왜 3개 노드만으로는 부족할 수도 있는가?:

자원 경합: 3개 노드의 총 자원이 일괄전송시스템 배치 작업이 피크 시 필요로 하는 자원과 다른 모든 서비스 Pod가 동시에 필요로 하는 자원의 합보다 적다면 자원 경합이 발생하고 성능 문제가 생깁니다.
배치 작업 특성: 일괄전송시스템(TainBat)은 CPU, 메모리, 디스크 I/O를 집중적으로 사용할 수 있습니다. 만약 배치 작업이 특정 시간에 집중적으로 실행되는데 3개 노드의 자원이 이를 감당하기에 부족하다면, 배치 작업 완료 시간이 지연되거나 다른 서비스에 영향을 줄 수 있습니다.
총 Pod 개수: 3개 노드에 할당 가능한 Pod의 최대 개수는 노드의 크기와 Pod의 자원 요청량에 따라 제한됩니다. 실행해야 할 배치 작업 Pod의 수나 다른 서비스 Pod의 수가 많다면 3개 노드로는 물리적인 Pod 배치 공간이 부족할 수 있습니다.
어떻게 결정해야 하는가?:

자원 프로파일링: 일괄전송시스템 배치 작업이 실행될 때 실제로 어느 정도의 CPU, 메모리, 디스크 I/O를 사용하는지 상세히 측정(프로파일링)합니다.
총 자원 요구량 예측: 시스템의 다른 모든 구성 요소 Pod들이 정상 상태 및 피크 상태에서 필요로 하는 자원량을 합산합니다.
부하 테스트: 일괄전송시스템 배치 작업이 실행되는 시나리오를 포함한 E2E 부하 테스트를 수행하여, 실제 부하 하에서 3개 노드 구성이 성능 목표를 만족하는지 확인합니다.
모니터링: 시스템 배포 후 노드 및 Pod의 CPU, 메모리, 디스크 I/O 사용률을 지속적으로 모니터링하여 자원이 부족해지는 시점을 파악합니다.
요약: 3개 이상의 워커 노드는 고가용성을 위한 시작점이며 Kubernetes 클러스터 구축의 일반적인 최소 권장 구성이지만, 여러분의 "swap-reporting-mvp" 시스템, 특히 자원 소모가 클 수 있는 일괄전송시스템의 실제 부하를 감당하기에 충분한지는 해당 시스템의 자원 요구량을 측정하고 다른 서비스와의 자원 경합을 고려해야만 판단할 수 있습니다. 부하 테스트와 운영 중 모니터링을 통해 실제 필요한 노드 수를 결정하고, 필요에 따라 노드를 확장해야 합니다.
