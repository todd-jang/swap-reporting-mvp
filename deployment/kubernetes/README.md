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
